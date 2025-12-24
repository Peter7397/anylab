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

        # Accept either a log file or a prompt-only query (require at least one)
        if not log_content and not query:
            return bad_request_response('Either log_content or query is required')
        
        # Get language preference from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-US')
        language = accept_language.split(',')[0].strip() if accept_language else 'en-US'
        is_chinese = 'zh' in language.lower()

        # Call Ollama to analyze the log file
        # Use consistent settings keys across the codebase
        ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434')
        from ai_assistant.utils.model_settings import get_ollama_model
        model = get_ollama_model()
        request_timeout = getattr(settings, 'OLLAMA_REQUEST_TIMEOUT', 120)
        default_max_tokens = getattr(settings, 'OLLAMA_DEFAULT_MAX_TOKENS', 256)
        num_ctx = getattr(settings, 'OLLAMA_NUM_CTX', 1024)

        # Preprocess large logs to keep prompt within reasonable bounds
        # Keep the last 20k chars and include up to 100 lines containing common error keywords
        def preprocess_log(content: str) -> str:
            try:
                max_chars = 20000
                lines = content.split('\n')
                tail = content[-max_chars:] if len(content) > max_chars else content

                import re as _re
                error_lines = [ln for ln in lines if _re.search(r"error|exception|traceback|fail|critical|fatal", ln, _re.IGNORECASE)]
                error_preview = '\n'.join(error_lines[-100:]) if error_lines else ''

                if error_preview:
                    return (
                        "[NOTE] Log was large; included last 20k chars and last 100 matched error lines.\n\n"
                        "[ERROR LINES]\n" + error_preview + "\n\n[TAIL]\n" + tail
                    )
                return tail
            except Exception:
                return content

        reduced_log = preprocess_log(log_content) if log_content else ''
        
        # Create system prompt and user prompt separately for better language control
        if is_chinese:
            system_prompt = "你是一位专业的系统管理员和故障排查专家。请用中文提供详细的分析和建议，保持专业、准确、可操作。"
            user_prompt = f"""请分析以下日志文件内容并提供详细的故障排查建议。

用户问题：{query if query else "请分析此日志文件并提供故障排查建议"}

日志文件内容：
{reduced_log if reduced_log else "[未提供日志文件]"}

请提供：
1. 日志内容的简要分析
2. 问题的严重程度（低/中/高）
3. 具体可执行的解决建议
4. 需要立即关注的警告或关键问题

请以JSON格式回复，结构如下：
{{
  "analysis": "日志文件的详细分析",
  "severity": "low|medium|high",
  "suggestions": [
    "建议 1",
    "建议 2",
    "建议 3"
  ]
}}

请具体、可操作，并优先处理最关键的问题。"""
        else:
            system_prompt = "You are an expert system administrator and troubleshooting specialist. Provide detailed analysis and suggestions in English, being professional, accurate, and actionable."
            user_prompt = f"""Analyze the following log file content and provide detailed troubleshooting suggestions.

User Query: {query if query else "Please analyze this log file and provide troubleshooting suggestions"}

Log File Content:
{reduced_log if reduced_log else "[No log file provided]"}

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

        # Call Ollama using /api/chat for better language control
        response = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Low temperature for more deterministic analysis
                    "top_p": 0.9,
                    "num_predict": max(default_max_tokens, 1000),  # ensure sufficient budget for structured output
                    "num_ctx": num_ctx
                }
            },
            timeout=request_timeout
        )
        
        response.raise_for_status()
        response_data = response.json()
        # Extract message content from chat API response
        generated_text = response_data.get('message', {}).get('content', '') or response_data.get('response', '')
        
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
            "log_length": len(log_content or ''),
            "lines_analyzed": len((log_content or '').split('\n')),
            "used_truncation": bool(log_content and reduced_log and reduced_log != log_content)
        }
        
        BaseViewMixin.log_response(result, 'analyze_logs')
        return success_response("Log analysis completed successfully", result)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Ollama: {e}")
        return Response({
            "status": "error",
            "message": f"Failed to analyze log: {str(e)}",
            "error": str(e),
            "analysis": "Could not connect to AI service. Please check your connection.",
            "suggestions": [
                "Check if Ollama service is running",
                "Verify OLLAMA_API_URL setting matches the reachable host",
                "Try again in a few moments"
            ],
            "severity": "low"
        }, status=500)
        
    except Exception as e:
        logger.error(f"Error analyzing log file: {e}")
        return BaseViewMixin.handle_error(e, 'analyze_logs')

