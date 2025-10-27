"""
Troubleshooting AI Views - Log Analysis
"""
import logging
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .base_views import BaseViewMixin, success_response, bad_request_response

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_logs(request):
    """
    Analyze log files using AI to provide troubleshooting suggestions
    """
    try:
        BaseViewMixin.log_request(request, 'analyze_logs')
        
        query = request.data.get('query', '')
        log_content = request.data.get('log_content', '')
        
        if not log_content:
            return bad_request_response('Log content is required')
        
        # Call Ollama to analyze the log file
        ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:latest')
        
        # Create a comprehensive prompt for log analysis
        prompt = f"""You are an expert system administrator and troubleshooting specialist.

Analyze the following log file content and provide detailed troubleshooting suggestions.

User Query: {query if query else "Please analyze this log file and provide troubleshooting suggestions"}

Log File Content:
{log_content}

Please provide:
1. A brief analysis of what the log indicates
2. The severity of the issues (low/medium/high)
3. Specific actionable suggestions to resolve the problems
4. Any warnings or critical issues that need immediate attention

Format your response as JSON with the following structure:
{{
  "analysis": "Detailed analysis of the log file",
  "severity": "low|medium|high",
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2",
    "Suggestion 3"
  ]
}}

Be specific, actionable, and prioritize the most critical issues."""

        # Call Ollama
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Low temperature for more deterministic analysis
                    "top_p": 0.9,
                    "num_predict": 2000
                }
            },
            timeout=60
        )
        
        response.raise_for_status()
        generated_text = response.json().get('response', '')
        
        # Try to parse JSON from the response
        import json
        import re
        
        # Extract JSON if present
        json_match = re.search(r'\{[\s\S]*\}', generated_text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                analysis = parsed.get('analysis', generated_text)
                suggestions = parsed.get('suggestions', [])
                severity = parsed.get('severity', 'medium')
            except:
                analysis = generated_text
                suggestions = []
                severity = 'medium'
        else:
            # Parse manually if JSON extraction fails
            analysis = generated_text
            suggestions = []
            severity = 'medium'
            
            # Try to extract suggestions from the text
            suggestion_patterns = [
                r'(\d+)\.\s+([^\n]+)',
                r'[-•]\s+([^\n]+)',
                r'^\s*\*\s+(.+?)(?:\n|$)'
            ]
            
            for pattern in suggestion_patterns:
                matches = re.findall(pattern, generated_text, re.MULTILINE)
                if matches:
                    suggestions = [match[1] if isinstance(match, tuple) else match for match in matches][:5]
                    break
        
        result = {
            "analysis": analysis,
            "suggestions": suggestions,
            "severity": severity,
            "log_length": len(log_content),
            "lines_analyzed": len(log_content.split('\n'))
        }
        
        BaseViewMixin.log_response(result, 'analyze_logs')
        return success_response("Log analysis completed successfully", result)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Ollama: {e}")
        return Response({
            "status": "error",
            "message": f"Failed to analyze log: {str(e)}",
            "analysis": "Could not connect to AI service. Please check your connection.",
            "suggestions": [
                "Check if Ollama service is running",
                "Verify network connectivity",
                "Try again in a few moments"
            ],
            "severity": "low"
        }, status=500)
        
    except Exception as e:
        logger.error(f"Error analyzing log file: {e}")
        return BaseViewMixin.handle_error(e, 'analyze_logs')

