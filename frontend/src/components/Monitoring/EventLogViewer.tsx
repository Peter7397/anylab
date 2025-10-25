import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { 
  Search, 
  RefreshCw, 
  Filter,
  Calendar,
  Server,
  AlertTriangle,
  Info,
  XCircle
} from 'lucide-react';
import * as ApiService from '../../services/api';

interface EventLog {
  id: number;
  event_id: number;
  event_level: string;
  event_source: string;
  event_message: string;
  event_time_created: string;
  system_name: string;
  event_log_name: string;
  event_provider_name: string;
  event_category: string;
  event_data: any;
}

const EventLogViewer: React.FC = () => {
  const [events, setEvents] = useState<EventLog[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<EventLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [systemFilter, setSystemFilter] = useState<string>('all');
  const [systems, setSystems] = useState<string[]>([]);

  useEffect(() => {
    fetchEvents();
    fetchSystems();
  }, []);

  useEffect(() => {
    // Only call filterEvents if events is an array
    if (Array.isArray(events)) {
      filterEvents();
    } else {
      setFilteredEvents([]);
    }
  }, [events, searchTerm, levelFilter, sourceFilter, systemFilter]);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await ApiService.apiClient.get<EventLog[]>('/monitoring/api/events/');
      // Ensure we set an array, even if the API returns something else
      const eventsData = Array.isArray(response.data) ? response.data : [];
      setEvents(eventsData);
    } catch (err) {
      setError('Failed to load events');
      console.error('Error fetching events:', err);
      // Set empty array on error
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystems = async () => {
    try {
      const response = await ApiService.apiClient.get<any[]>('/monitoring/dashboard/systems/');
      // Ensure we have an array and map safely
      const systemsData = Array.isArray(response.data) ? response.data : [];
      const systemNames = systemsData.map((system: any) => system.name);
      setSystems(systemNames);
    } catch (err) {
      console.error('Error fetching systems:', err);
      setSystems([]);
    }
  };

  const filterEvents = () => {
    // Ensure events is an array
    if (!Array.isArray(events)) {
      setFilteredEvents([]);
      return;
    }

    let filtered = events;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(event =>
        event.event_message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.system_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.event_provider_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.event_id.toString().includes(searchTerm)
      );
    }

    // Filter by level
    if (levelFilter !== 'all') {
      filtered = filtered.filter(event => event.event_level === levelFilter);
    }

    // Filter by source
    if (sourceFilter !== 'all') {
      filtered = filtered.filter(event => event.event_source === sourceFilter);
    }

    // Filter by system
    if (systemFilter !== 'all') {
      filtered = filtered.filter(event => event.system_name === systemFilter);
    }

    setFilteredEvents(filtered);
  };

  const getEventLevelBadge = (level: string) => {
    switch (level) {
      case 'Critical':
        return <Badge variant="destructive">Critical</Badge>;
      case 'Error':
        return <Badge variant="default" className="bg-red-100 text-red-800">Error</Badge>;
      case 'Warning':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case 'Information':
        return <Badge variant="outline">Info</Badge>;
      default:
        return <Badge variant="outline">{level}</Badge>;
    }
  };

  const getEventLevelIcon = (level: string) => {
    switch (level) {
      case 'Critical':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'Error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'Warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'Information':
        return <Info className="h-4 w-4 text-blue-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const truncateMessage = (message: string, maxLength: number = 200) => {
    if (message.length <= maxLength) return message;
    return message.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Event Log Viewer</h1>
          <p className="text-muted-foreground">
            View and search Windows Event Log entries from monitored systems
          </p>
        </div>
        <Button onClick={fetchEvents}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="lg:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search events..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select value={levelFilter} onValueChange={setLevelFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Event Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="Critical">Critical</SelectItem>
                <SelectItem value="Error">Error</SelectItem>
                <SelectItem value="Warning">Warning</SelectItem>
                <SelectItem value="Information">Information</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={sourceFilter} onValueChange={setSourceFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Event Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="System">System</SelectItem>
                <SelectItem value="Application">Application</SelectItem>
                <SelectItem value="Security">Security</SelectItem>
                <SelectItem value="Setup">Setup</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={systemFilter} onValueChange={setSystemFilter}>
              <SelectTrigger>
                <SelectValue placeholder="System" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Systems</SelectItem>
                {Array.isArray(systems) && systems.map((system) => (
                  <SelectItem key={system} value={system}>{system}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Events List */}
      <div className="space-y-4">
        {Array.isArray(filteredEvents) && filteredEvents.map((event) => (
          <Card key={event.id} className="hover:shadow-md transition-shadow">
            <CardContent className="pt-6">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  {getEventLevelIcon(event.event_level)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-sm font-mono text-muted-foreground">
                      Event ID: {event.event_id}
                    </span>
                    {getEventLevelBadge(event.event_level)}
                    <Badge variant="outline">{event.event_source}</Badge>
                  </div>
                  
                  <h3 className="font-medium mb-2">
                    {truncateMessage(event.event_message, 150)}
                  </h3>
                  
                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <Server className="h-3 w-3" />
                      <span>{event.system_name}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar className="h-3 w-3" />
                      <span>{new Date(event.event_time_created).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span>•</span>
                      <span>{getTimeAgo(event.event_time_created)}</span>
                    </div>
                    {event.event_provider_name && (
                      <div className="flex items-center space-x-1">
                        <span>•</span>
                        <span>Provider: {event.event_provider_name}</span>
                      </div>
                    )}
                  </div>
                  
                  {event.event_message.length > 150 && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
                        Show full message
                      </summary>
                      <div className="mt-2 p-3 bg-gray-50 rounded text-sm font-mono whitespace-pre-wrap">
                        {event.event_message}
                      </div>
                    </details>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {(!Array.isArray(filteredEvents) || filteredEvents.length === 0) && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium">No events found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || levelFilter !== 'all' || sourceFilter !== 'all' || systemFilter !== 'all'
                    ? 'Try adjusting your search or filters'
                    : 'No events are currently available'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Event Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{Array.isArray(events) ? events.length : 0}</div>
              <div className="text-sm text-muted-foreground">Total Events</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {Array.isArray(events) ? events.filter(e => e.event_level === 'Critical').length : 0}
              </div>
              <div className="text-sm text-muted-foreground">Critical</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Array.isArray(events) ? events.filter(e => e.event_level === 'Error').length : 0}
              </div>
              <div className="text-sm text-muted-foreground">Errors</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {Array.isArray(events) ? events.filter(e => e.event_level === 'Warning').length : 0}
              </div>
              <div className="text-sm text-muted-foreground">Warnings</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {Array.isArray(events) ? events.filter(e => e.event_level === 'Information').length : 0}
              </div>
              <div className="text-sm text-muted-foreground">Info</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EventLogViewer;
