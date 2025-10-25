from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # Existing monitoring endpoints
    path('systems/', views.system_list, name='system_list'),
    
    # SysMon Agent endpoints (no authentication required for agent communication)
    path('sysmon/alerts/', views.sysmon_alert_endpoint, name='sysmon_alerts'),
    path('sysmon/metrics/', views.sysmon_metrics_endpoint, name='sysmon_metrics'),
    
    # SysMon Agent management endpoints (authenticated)
    path('sysmon/agents/', views.sysmon_agents_list, name='sysmon_agents_list'),
    path('sysmon/agents/<str:hostname>/', views.sysmon_agent_detail, name='sysmon_agent_detail'),
    path('sysmon/agents/<str:hostname>/metrics/', views.sysmon_agent_metrics, name='sysmon_agent_metrics'),
    
    # AppMon Agent endpoints (no authentication required for agent communication)
    path('appmon/alerts/', views.appmon_alert_endpoint, name='appmon_alerts'),
    path('appmon/metrics/', views.appmon_metrics_endpoint, name='appmon_metrics'),
    
    # AppMon Agent management endpoints (authenticated)
    path('appmon/agents/', views.appmon_agents_list, name='appmon_agents_list'),
    path('appmon/agents/<int:application_id>/', views.appmon_agent_detail, name='appmon_agent_detail'),
    path('appmon/agents/<int:application_id>/metrics/', views.appmon_agent_metrics, name='appmon_agent_metrics'),
    path('appmon/alerts/', views.appmon_alerts_list, name='appmon_alerts_list'),
    path('appmon/alerts/<int:alert_id>/acknowledge/', views.appmon_alert_acknowledge, name='appmon_alert_acknowledge'),
] 