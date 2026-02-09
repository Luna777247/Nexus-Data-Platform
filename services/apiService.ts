/**
 * Nexus Data Platform - API Service
 * Client-side API calls to FastAPI backend
 */

import { TravelLocation, WarehouseRecord } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Check API health status
 */
export async function checkApiHealth(): Promise<{ status: string; services: any }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`API health check failed: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API health check error:', error);
    return {
      status: 'unhealthy',
      services: {
        api: '❌ Disconnected',
        cache: '❌ Unavailable'
      }
    };
  }
}

/**
 * Get tour recommendations
 */
export async function getRecommendations(userId: number, limit: number = 5): Promise<TravelLocation[]> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/recommendations?user_id=${userId}&limit=${limit}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recommendations: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Convert API response to TravelLocation format
    return (data.recommendations || []).map((rec: any) => ({
      id: rec.id,
      name: rec.name,
      city: rec.region || 'Unknown',
      category: rec.tags?.[0] || 'general',
      rating: rec.rating || 0,
      reviewsCount: Math.floor(Math.random() * 1000) + 100, // Mock data
      avgPrice: rec.price || 0,
      tags: rec.tags || [],
      matchScore: rec.match_score || 0,
      recommendationType: rec.reason === 'Trending' ? 'Hybrid' : 'Content-Based'
    }));
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    // Return mock data on error
    return getMockRecommendations(limit);
  }
}

/**
 * Get tours with optional filters
 */
export async function getTours(
  region?: string, 
  minPrice?: number, 
  maxPrice?: number, 
  limit: number = 10
): Promise<any[]> {
  try {
    const params = new URLSearchParams();
    if (region) params.append('region', region);
    if (minPrice !== undefined) params.append('min_price', minPrice.toString());
    if (maxPrice !== undefined) params.append('max_price', maxPrice.toString());
    params.append('limit', limit.toString());
    
    const response = await fetch(`${API_BASE_URL}/api/v1/tours?${params.toString()}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch tours: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.data || [];
  } catch (error) {
    console.error('Error fetching tours:', error);
    return getMockTours(limit);
  }
}

/**
 * Get regional statistics
 */
export async function getRegionalStats(region?: string): Promise<any[]> {
  try {
    const url = region 
      ? `${API_BASE_URL}/api/v1/analytics/regional-stats?region=${region}`
      : `${API_BASE_URL}/api/v1/analytics/regional-stats`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch regional stats: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.data || [];
  } catch (error) {
    console.error('Error fetching regional stats:', error);
    return getMockRegionalStats();
  }
}

/**
 * Convert tour data to TravelLocation format
 */
export function convertTourToTravelLocation(tour: any): TravelLocation {
  return {
    id: tour.id,
    name: tour.name,
    city: tour.region || 'Unknown',
    category: tour.tags?.[0] || 'general',
    rating: tour.rating || 0,
    reviewsCount: Math.floor(Math.random() * 1000) + 100,
    avgPrice: tour.price || 0,
    tags: tour.tags || [],
    matchScore: 0.75,
    recommendationType: 'Content-Based'
  };
}

/**
 * Convert regional stats to WarehouseRecord format
 */
export function convertStatsToWarehouseRecord(stats: any, index: number): WarehouseRecord {
  return {
    id: index,
    timestamp: new Date().toISOString(),
    region: stats.region || 'Unknown',
    category: 'tourism',
    metricValue: stats.total_revenue || 0,
    qualityScore: Math.min(100, (stats.conversion_rate || 0) * 100),
    transformationLog: `Processed ${stats.total_bookings || 0} bookings`
  };
}

// ============================================
// MOCK DATA FUNCTIONS (Fallback)
// ============================================

function getMockRecommendations(limit: number): TravelLocation[] {
  const mockData: TravelLocation[] = [
    {
      id: 't1',
      name: 'Hanoi City Tour',
      city: 'Hanoi',
      category: 'cultural',
      rating: 4.8,
      reviewsCount: 523,
      avgPrice: 59.99,
      tags: ['cultural', 'city', 'history'],
      matchScore: 0.92,
      recommendationType: 'Hybrid'
    },
    {
      id: 't2',
      name: 'Halong Bay Cruise',
      city: 'Quang Ninh',
      category: 'adventure',
      rating: 4.9,
      reviewsCount: 876,
      avgPrice: 199.99,
      tags: ['adventure', 'nature', 'sea'],
      matchScore: 0.88,
      recommendationType: 'Collaborative'
    },
    {
      id: 't3',
      name: 'Sapa Trekking',
      city: 'Lao Cai',
      category: 'hiking',
      rating: 4.7,
      reviewsCount: 345,
      avgPrice: 149.99,
      tags: ['hiking', 'nature', 'mountain'],
      matchScore: 0.85,
      recommendationType: 'Content-Based'
    },
    {
      id: 't4',
      name: 'Mekong Delta Discovery',
      city: 'Can Tho',
      category: 'cultural',
      rating: 4.6,
      reviewsCount: 289,
      avgPrice: 89.99,
      tags: ['cultural', 'river', 'local'],
      matchScore: 0.82,
      recommendationType: 'Hybrid'
    },
    {
      id: 't5',
      name: 'Hoi An Ancient Town',
      city: 'Quang Nam',
      category: 'cultural',
      rating: 4.9,
      reviewsCount: 654,
      avgPrice: 79.99,
      tags: ['cultural', 'history', 'shopping'],
      matchScore: 0.90,
      recommendationType: 'Collaborative'
    }
  ];
  
  return mockData.slice(0, limit);
}

function getMockTours(limit: number): any[] {
  const mockTours = [
    {
      id: 't1',
      name: 'Hanoi City Tour',
      region: 'VN',
      price: 59.99,
      rating: 4.8,
      tags: ['cultural', 'city', 'history']
    },
    {
      id: 't2',
      name: 'Halong Bay Cruise',
      region: 'VN',
      price: 199.99,
      rating: 4.9,
      tags: ['adventure', 'nature', 'sea']
    },
    {
      id: 't3',
      name: 'Sapa Trekking',
      region: 'VN',
      price: 149.99,
      rating: 4.7,
      tags: ['hiking', 'nature', 'mountain']
    },
    {
      id: 't4',
      name: 'Bangkok Night Market',
      region: 'TH',
      price: 45.99,
      rating: 4.5,
      tags: ['shopping', 'food', 'night']
    },
    {
      id: 't5',
      name: 'Phuket Beach Resort',
      region: 'TH',
      price: 299.99,
      rating: 4.8,
      tags: ['beach', 'resort', 'relaxation']
    }
  ];
  
  return mockTours.slice(0, limit);
}

function getMockRegionalStats(): any[] {
  return [
    {
      region: 'VN',
      total_bookings: 523,
      total_revenue: 31245.67,
      unique_users: 412,
      avg_booking_value: 59.78,
      conversion_rate: 12.5
    },
    {
      region: 'TH',
      total_bookings: 789,
      total_revenue: 56789.23,
      unique_users: 634,
      avg_booking_value: 71.94,
      conversion_rate: 15.2
    },
    {
      region: 'SG',
      total_bookings: 345,
      total_revenue: 23456.12,
      unique_users: 278,
      avg_booking_value: 67.98,
      conversion_rate: 10.8
    },
    {
      region: 'ID',
      total_bookings: 456,
      total_revenue: 34567.89,
      unique_users: 367,
      avg_booking_value: 75.81,
      conversion_rate: 11.3
    }
  ];
}
