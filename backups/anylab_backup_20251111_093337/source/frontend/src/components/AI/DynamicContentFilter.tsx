/**
 * Dynamic Content Filtering Frontend Components for AnyLab
 *
 * This module provides React components for intelligent content filtering
 * that adapts to both General Agilent Products and Lab Informatics Focus modes.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Search,
    Filter,
    SortAsc,
    SortDesc,
    Calendar,
    FileText,
    Tag,
    Star,
    Clock,
    TrendingUp,
    Download,
    Eye,
    ChevronDown,
    ChevronUp,
    X,
    Save,
    Bookmark,
    RefreshCw,
    Settings,
    Zap,
    AlertTriangle,
    CheckCircle,
    Info,
    FilterX
} from 'lucide-react';

// Types
interface FilterCriteria {
    filterType: string;
    fieldName: string;
    operator: string;
    value: any;
    weight: number;
    required: boolean;
}

interface SearchContext {
    organizationMode: 'general' | 'lab-informatics';
    userRole?: string;
    userPreferences: Record<string, any>;
    searchHistory: string[];
    currentPage: string;
    sessionId?: string;
    deviceType: string;
}

interface FilterResult {
    documentId: string;
    relevanceScore: number;
    matchReasons: string[];
    metadata: Record<string, any>;
    snippet?: string;
}

interface FilterResponse {
    results: FilterResult[];
    totalCount: number;
    page: number;
    pageSize: number;
    totalPages: number;
    organizationMode: string;
    appliedFilters: FilterCriteria[];
    sortOrder: string;
    searchQuery?: string;
    context?: SearchContext;
    generatedAt: string;
}

// Filter Types
const FILTER_TYPES = {
    TEXT_SEARCH: 'text_search',
    CATEGORY_FILTER: 'category_filter',
    DATE_RANGE: 'date_range',
    FILE_TYPE: 'file_type',
    PRODUCT_FILTER: 'product_filter',
    SEVERITY_FILTER: 'severity_filter',
    QUALITY_FILTER: 'quality_filter',
    USAGE_FILTER: 'usage_filter',
    SOURCE_FILTER: 'source_filter',
    TAG_FILTER: 'tag_filter',
    CUSTOM_FILTER: 'custom_filter'
};

const SORT_ORDERS = {
    RELEVANCE: 'relevance',
    DATE_NEWEST: 'date_newest',
    DATE_OLDEST: 'date_oldest',
    POPULARITY: 'popularity',
    QUALITY_SCORE: 'quality_score',
    ALPHABETICAL: 'alphabetical',
    FILE_SIZE: 'file_size',
    PAGE_COUNT: 'page_count'
};

// Document Types for each mode
const GENERAL_DOCUMENT_TYPES = [
    { value: 'USER_MANUAL', label: 'User Manual', icon: FileText },
    { value: 'TECHNICAL_SPECIFICATION', label: 'Technical Specification', icon: FileText },
    { value: 'INSTALLATION_GUIDE', label: 'Installation Guide', icon: FileText },
    { value: 'MAINTENANCE_GUIDE', label: 'Maintenance Guide', icon: FileText },
    { value: 'PRODUCT_CATALOG', label: 'Product Catalog', icon: FileText },
    { value: 'APPLICATION_NOTE', label: 'Application Note', icon: FileText },
    { value: 'WHITE_PAPER', label: 'White Paper', icon: FileText }
];

const LAB_INFORMATICS_DOCUMENT_TYPES = [
    { value: 'SSB_KPR', label: 'SSB/KPR', icon: AlertTriangle },
    { value: 'TROUBLESHOOTING_GUIDE', label: 'Troubleshooting Guide', icon: AlertTriangle },
    { value: 'MAINTENANCE_PROCEDURE', label: 'Maintenance Procedure', icon: Settings },
    { value: 'CALIBRATION_PROCEDURE', label: 'Calibration Procedure', icon: Settings },
    { value: 'CONFIGURATION_GUIDE', label: 'Configuration Guide', icon: Settings },
    { value: 'BEST_PRACTICE_GUIDE', label: 'Best Practice Guide', icon: CheckCircle },
    { value: 'COMMUNITY_SOLUTION', label: 'Community Solution', icon: Info },
    { value: 'VIDEO_TUTORIAL', label: 'Video Tutorial', icon: FileText },
    { value: 'WEBINAR_RECORDING', label: 'Webinar Recording', icon: FileText }
];

// Product Categories for each mode
const GENERAL_PRODUCT_CATEGORIES = [
    { value: 'GAS_CHROMATOGRAPHY', label: 'Gas Chromatography', icon: Zap },
    { value: 'LIQUID_CHROMATOGRAPHY', label: 'Liquid Chromatography', icon: Zap },
    { value: 'MASS_SPECTROMETRY', label: 'Mass Spectrometry', icon: Zap },
    { value: 'NMR_SYSTEMS', label: 'NMR Systems', icon: Zap },
    { value: 'SPECTROSCOPY', label: 'Spectroscopy', icon: Zap },
    { value: 'VACUUM_TECHNOLOGIES', label: 'Vacuum Technologies', icon: Zap },
    { value: 'LIFE_SCIENCES', label: 'Life Sciences', icon: Zap },
    { value: 'DIAGNOSTICS', label: 'Diagnostics', icon: Zap }
];

const LAB_INFORMATICS_PRODUCT_CATEGORIES = [
    { value: 'OPENLAB_CDS', label: 'OpenLab CDS', icon: FileText },
    { value: 'OPENLAB_ECM', label: 'OpenLab ECM', icon: FileText },
    { value: 'OPENLAB_ELN', label: 'OpenLab ELN', icon: FileText },
    { value: 'OPENLAB_SERVER', label: 'OpenLab Server', icon: FileText },
    { value: 'MASSHUNTER_WORKSTATION', label: 'MassHunter Workstation', icon: FileText },
    { value: 'MASSHUNTER_QUANTITATIVE', label: 'MassHunter Quantitative', icon: FileText },
    { value: 'MASSHUNTER_QUALITATIVE', label: 'MassHunter Qualitative', icon: FileText },
    { value: 'MASSHUNTER_BIO_CONFIRM', label: 'MassHunter BioConfirm', icon: FileText },
    { value: 'MASSHUNTER_METABOLOMICS', label: 'MassHunter Metabolomics', icon: FileText },
    { value: 'VNMRJ_CURRENT', label: 'VNMRJ Current', icon: FileText },
    { value: 'VNMRJ_LEGACY', label: 'VNMRJ Legacy', icon: FileText },
    { value: 'VNMR_LEGACY', label: 'VNMR Legacy', icon: FileText }
];

// Main Filter Component
interface DynamicContentFilterProps {
    organizationMode: 'general' | 'lab-informatics';
    onResultsChange: (results: FilterResult[]) => void;
    onLoadingChange: (loading: boolean) => void;
    initialSearchQuery?: string;
    className?: string;
}

export const DynamicContentFilter: React.FC<DynamicContentFilterProps> = ({
    organizationMode,
    onResultsChange,
    onLoadingChange,
    initialSearchQuery = '',
    className = ''
}) => {
    // State
    const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
    const [filters, setFilters] = useState<FilterCriteria[]>([]);
    const [sortOrder, setSortOrder] = useState(SORT_ORDERS.RELEVANCE);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<FilterResult[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [totalPages, setTotalPages] = useState(0);
    const [suggestions, setSuggestions] = useState<Record<string, string[]>>({});
    const [recentSearches, setRecentSearches] = useState<string[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    // Get current document types and product categories based on mode
    const documentTypes = useMemo(() => {
        return organizationMode === 'general' ? GENERAL_DOCUMENT_TYPES : LAB_INFORMATICS_DOCUMENT_TYPES;
    }, [organizationMode]);

    const productCategories = useMemo(() => {
        return organizationMode === 'general' ? GENERAL_PRODUCT_CATEGORIES : LAB_INFORMATICS_PRODUCT_CATEGORIES;
    }, [organizationMode]);

    // Load suggestions and recent searches
    useEffect(() => {
        loadSuggestions();
        loadRecentSearches();
    }, [organizationMode]);

    // Perform search when filters change
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            performSearch();
        }, 300); // Debounce search

        return () => clearTimeout(timeoutId);
    }, [searchQuery, filters, sortOrder, currentPage, pageSize, organizationMode]);

    const loadSuggestions = async () => {
        try {
            const response = await fetch(`/api/ai/filter-suggestions/?mode=${organizationMode}`);
            if (response.ok) {
                const data = await response.json();
                setSuggestions(data);
            }
        } catch (error) {
            console.error('Error loading suggestions:', error);
        }
    };

    const loadRecentSearches = () => {
        const saved = localStorage.getItem(`anylab_recent_searches_${organizationMode}`);
        if (saved) {
            setRecentSearches(JSON.parse(saved));
        }
    };

    const saveRecentSearch = (query: string) => {
        if (query.trim()) {
            const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 10);
            setRecentSearches(updated);
            localStorage.setItem(`anylab_recent_searches_${organizationMode}`, JSON.stringify(updated));
        }
    };

    const performSearch = async () => {
        setLoading(true);
        onLoadingChange(true);

        try {
            const searchContext: SearchContext = {
                organizationMode,
                userRole: 'user', // This would come from auth context
                userPreferences: {},
                searchHistory: recentSearches,
                currentPage: window.location.pathname,
                sessionId: 'session_123', // This would be generated
                deviceType: 'desktop'
            };

            const requestBody = {
                search_query: searchQuery,
                organization_mode: organizationMode,
                filters: filters,
                sort_order: sortOrder,
                page: currentPage,
                page_size: pageSize,
                context: searchContext
            };

            const response = await fetch('/api/ai/filter-documents/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('anylab_token')}`
                },
                body: JSON.stringify(requestBody)
            });

            if (response.ok) {
                const data: FilterResponse = await response.json();
                setResults(data.results);
                setTotalCount(data.totalCount);
                setTotalPages(data.totalPages);
                onResultsChange(data.results);

                // Save search to history
                if (searchQuery.trim()) {
                    saveRecentSearch(searchQuery);
                }
            } else {
                console.error('Search failed:', response.statusText);
            }
        } catch (error) {
            console.error('Error performing search:', error);
        } finally {
            setLoading(false);
            onLoadingChange(false);
        }
    };

    const addFilter = (filterType: string, fieldName: string, operator: string, value: any) => {
        const newFilter: FilterCriteria = {
            filterType,
            fieldName,
            operator,
            value,
            weight: 1.0,
            required: false
        };
        setFilters(prev => [...prev, newFilter]);
    };

    const removeFilter = (index: number) => {
        setFilters(prev => prev.filter((_, i) => i !== index));
    };

    const clearAllFilters = () => {
        setFilters([]);
        setSearchQuery('');
    };

    const handleSearchInputChange = (value: string) => {
        setSearchQuery(value);
        setShowSuggestions(value.length > 0);
    };

    const handleSuggestionClick = (suggestion: string) => {
        setSearchQuery(suggestion);
        setShowSuggestions(false);
    };

    return (
        <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
            {/* Search Bar */}
            <div className="p-4 border-b border-gray-200">
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => handleSearchInputChange(e.target.value)}
                        placeholder={`Search ${organizationMode === 'general' ? 'Agilent products' : 'Lab Informatics'}...`}
                        className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                    
                    {/* Suggestions Dropdown */}
                    {showSuggestions && (
                        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
                            {/* Recent Searches */}
                            {recentSearches.length > 0 && (
                                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                    Recent Searches
                                </div>
                            )}
                            {recentSearches.map((search, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSuggestionClick(search)}
                                    className="w-full text-left px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 flex items-center"
                                >
                                    <Clock className="h-4 w-4 mr-2 text-gray-400" />
                                    {search}
                                </button>
                            ))}
                            
                            {/* Document Type Suggestions */}
                            {suggestions.document_types && suggestions.document_types.length > 0 && (
                                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                    Document Types
                                </div>
                            )}
                            {suggestions.document_types?.map((type, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSuggestionClick(type)}
                                    className="w-full text-left px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 flex items-center"
                                >
                                    <FileText className="h-4 w-4 mr-2 text-gray-400" />
                                    {type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Filter Controls */}
            <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            <Filter className="h-4 w-4 mr-2" />
                            Advanced Filters
                            {showAdvancedFilters ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
                        </button>
                        
                        {filters.length > 0 && (
                            <button
                                onClick={clearAllFilters}
                                className="flex items-center px-3 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-300 rounded-md hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                            >
                                <FilterX className="h-4 w-4 mr-2" />
                                Clear All ({filters.length})
                            </button>
                        )}
                    </div>

                    <div className="flex items-center space-x-2">
                        <select
                            value={sortOrder}
                            onChange={(e) => setSortOrder(e.target.value)}
                            className="block w-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value={SORT_ORDERS.RELEVANCE}>Relevance</option>
                            <option value={SORT_ORDERS.DATE_NEWEST}>Newest First</option>
                            <option value={SORT_ORDERS.DATE_OLDEST}>Oldest First</option>
                            <option value={SORT_ORDERS.POPULARITY}>Most Popular</option>
                            <option value={SORT_ORDERS.QUALITY_SCORE}>Highest Quality</option>
                            <option value={SORT_ORDERS.ALPHABETICAL}>A-Z</option>
                        </select>
                        
                        <select
                            value={pageSize}
                            onChange={(e) => setPageSize(Number(e.target.value))}
                            className="block w-20 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value={10}>10</option>
                            <option value={20}>20</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                        </select>
                    </div>
                </div>

                {/* Active Filters */}
                {filters.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                        {filters.map((filter, index) => (
                            <div
                                key={index}
                                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                            >
                                <span className="mr-2">
                                    {filter.fieldName}: {filter.value}
                                </span>
                                <button
                                    onClick={() => removeFilter(index)}
                                    className="ml-1 text-blue-600 hover:text-blue-800"
                                >
                                    <X className="h-3 w-3" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {/* Advanced Filters */}
                {showAdvancedFilters && (
                    <AdvancedFilterPanel
                        organizationMode={organizationMode}
                        documentTypes={documentTypes}
                        productCategories={productCategories}
                        onAddFilter={addFilter}
                    />
                )}
            </div>

            {/* Results Summary */}
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                        {loading ? (
                            <div className="flex items-center">
                                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                Searching...
                            </div>
                        ) : (
                            <>
                                Found {totalCount.toLocaleString()} documents
                                {searchQuery && ` for "${searchQuery}"`}
                            </>
                        )}
                    </div>
                    
                    {totalPages > 1 && (
                        <div className="flex items-center space-x-2">
                            <button
                                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                disabled={currentPage === 1 || loading}
                                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Previous
                            </button>
                            
                            <span className="text-sm text-gray-600">
                                Page {currentPage} of {totalPages}
                            </span>
                            
                            <button
                                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                disabled={currentPage === totalPages || loading}
                                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// Advanced Filter Panel Component
interface AdvancedFilterPanelProps {
    organizationMode: 'general' | 'lab-informatics';
    documentTypes: Array<{ value: string; label: string; icon: any }>;
    productCategories: Array<{ value: string; label: string; icon: any }>;
    onAddFilter: (filterType: string, fieldName: string, operator: string, value: any) => void;
}

const AdvancedFilterPanel: React.FC<AdvancedFilterPanelProps> = ({
    organizationMode,
    documentTypes,
    productCategories,
    onAddFilter
}) => {
    const [selectedDocumentTypes, setSelectedDocumentTypes] = useState<string[]>([]);
    const [selectedProductCategories, setSelectedProductCategories] = useState<string[]>([]);
    const [qualityRange, setQualityRange] = useState<[number, number]>([0, 1]);
    const [dateRange, setDateRange] = useState<{ start: string; end: string }>({ start: '', end: '' });

    const applyDocumentTypeFilter = () => {
        if (selectedDocumentTypes.length > 0) {
            onAddFilter(FILTER_TYPES.CATEGORY_FILTER, 'document_type', 'in', selectedDocumentTypes);
        }
    };

    const applyProductCategoryFilter = () => {
        if (selectedProductCategories.length > 0) {
            onAddFilter(FILTER_TYPES.PRODUCT_FILTER, 'product_category', 'in', selectedProductCategories);
        }
    };

    const applyQualityFilter = () => {
        onAddFilter(FILTER_TYPES.QUALITY_FILTER, 'quality_score', 'greater_than', qualityRange[0]);
    };

    const applyDateRangeFilter = () => {
        if (dateRange.start && dateRange.end) {
            onAddFilter(FILTER_TYPES.DATE_RANGE, 'created_at', 'in', [dateRange.start, dateRange.end]);
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            {/* Document Type Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Document Type
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                    {documentTypes.map((type) => (
                        <label key={type.value} className="flex items-center">
                            <input
                                type="checkbox"
                                checked={selectedDocumentTypes.includes(type.value)}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        setSelectedDocumentTypes(prev => [...prev, type.value]);
                                    } else {
                                        setSelectedDocumentTypes(prev => prev.filter(t => t !== type.value));
                                    }
                                }}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <span className="ml-2 text-sm text-gray-700">{type.label}</span>
                        </label>
                    ))}
                </div>
                <button
                    onClick={applyDocumentTypeFilter}
                    disabled={selectedDocumentTypes.length === 0}
                    className="mt-2 w-full px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Apply Filter
                </button>
            </div>

            {/* Product Category Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    {organizationMode === 'general' ? 'Product Category' : 'Software Platform'}
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                    {productCategories.map((category) => (
                        <label key={category.value} className="flex items-center">
                            <input
                                type="checkbox"
                                checked={selectedProductCategories.includes(category.value)}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        setSelectedProductCategories(prev => [...prev, category.value]);
                                    } else {
                                        setSelectedProductCategories(prev => prev.filter(c => c !== category.value));
                                    }
                                }}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <span className="ml-2 text-sm text-gray-700">{category.label}</span>
                        </label>
                    ))}
                </div>
                <button
                    onClick={applyProductCategoryFilter}
                    disabled={selectedProductCategories.length === 0}
                    className="mt-2 w-full px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Apply Filter
                </button>
            </div>

            {/* Quality Score Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quality Score: {qualityRange[0].toFixed(1)} - {qualityRange[1].toFixed(1)}
                </label>
                <div className="space-y-2">
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={qualityRange[0]}
                        onChange={(e) => setQualityRange([Number(e.target.value), qualityRange[1]])}
                        className="w-full"
                    />
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={qualityRange[1]}
                        onChange={(e) => setQualityRange([qualityRange[0], Number(e.target.value)])}
                        className="w-full"
                    />
                </div>
                <button
                    onClick={applyQualityFilter}
                    className="mt-2 w-full px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                    Apply Filter
                </button>
            </div>

            {/* Date Range Filter */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Range
                </label>
                <div className="space-y-2">
                    <input
                        type="date"
                        value={dateRange.start}
                        onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        placeholder="Start date"
                    />
                    <input
                        type="date"
                        value={dateRange.end}
                        onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        placeholder="End date"
                    />
                </div>
                <button
                    onClick={applyDateRangeFilter}
                    disabled={!dateRange.start || !dateRange.end}
                    className="mt-2 w-full px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Apply Filter
                </button>
            </div>
        </div>
    );
};

// Filter Result Item Component
interface FilterResultItemProps {
    result: FilterResult;
    organizationMode: 'general' | 'lab-informatics';
    onDocumentClick: (documentId: string) => void;
}

export const FilterResultItem: React.FC<FilterResultItemProps> = ({
    result,
    organizationMode,
    onDocumentClick
}) => {
    const getDocumentTypeIcon = (documentType: string) => {
        const allTypes = [...GENERAL_DOCUMENT_TYPES, ...LAB_INFORMATICS_DOCUMENT_TYPES];
        const type = allTypes.find(t => t.value === documentType);
        return type?.icon || FileText;
    };

    const getDocumentTypeLabel = (documentType: string) => {
        const allTypes = [...GENERAL_DOCUMENT_TYPES, ...LAB_INFORMATICS_DOCUMENT_TYPES];
        const type = allTypes.find(t => t.value === documentType);
        return type?.label || documentType.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    const DocumentTypeIcon = getDocumentTypeIcon(result.metadata.document_type);

    return (
        <div
            onClick={() => onDocumentClick(result.documentId)}
            className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 cursor-pointer transition-colors"
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center mb-2">
                        <DocumentTypeIcon className="h-5 w-5 text-gray-400 mr-2" />
                        <span className="text-sm text-gray-500">
                            {getDocumentTypeLabel(result.metadata.document_type)}
                        </span>
                        <div className="ml-4 flex items-center space-x-4 text-sm text-gray-500">
                            <div className="flex items-center">
                                <Eye className="h-4 w-4 mr-1" />
                                {result.metadata.view_count || 0}
                            </div>
                            <div className="flex items-center">
                                <Download className="h-4 w-4 mr-1" />
                                {result.metadata.download_count || 0}
                            </div>
                            <div className="flex items-center">
                                <Star className="h-4 w-4 mr-1" />
                                {(result.metadata.user_rating || 0).toFixed(1)}
                            </div>
                        </div>
                    </div>
                    
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                        {result.metadata.title}
                    </h3>
                    
                    {result.snippet && (
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                            {result.snippet}
                        </p>
                    )}
                    
                    <div className="flex items-center justify-between text-sm text-gray-500">
                        <div className="flex items-center space-x-4">
                            <span>{formatFileSize(result.metadata.file_size || 0)}</span>
                            {result.metadata.page_count && (
                                <span>{result.metadata.page_count} pages</span>
                            )}
                            {result.metadata.updated_at && (
                                <span>Updated {formatDate(result.metadata.updated_at)}</span>
                            )}
                        </div>
                        
                        <div className="flex items-center">
                            <div className="flex items-center mr-2">
                                <TrendingUp className="h-4 w-4 mr-1" />
                                {(result.relevanceScore * 100).toFixed(0)}%
                            </div>
                        </div>
                    </div>
                    
                    {result.matchReasons.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                            {result.matchReasons.map((reason, index) => (
                                <span
                                    key={index}
                                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                                >
                                    {reason}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DynamicContentFilter;
