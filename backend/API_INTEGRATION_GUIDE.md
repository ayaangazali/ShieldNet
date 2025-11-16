# ShieldNet API Integration Guide

Guide for integrating the ShieldNet frontend with the FastAPI backend.

## Base Configuration

```typescript
// src/config/api.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Invoice Intake
  invoices: {
    upload: '/api/invoices/upload',
    list: '/api/invoices',
    get: (id: number) => `/api/invoices/${id}`,
    reanalyze: (id: number) => `/api/invoices/${id}/reanalyze`,
  },
  
  // Treasury
  treasury: {
    overview: '/api/treasury/overview',
    pay: (id: number) => `/api/treasury/pay/${id}`,
    autoPay: '/api/treasury/auto-pay',
    transactions: '/api/treasury/transactions',
    balance: '/api/treasury/balance',
  },
  
  // Threats
  threats: {
    report: '/api/threats/report',
    query: '/api/threats/query',
    list: '/api/threats/list',
    share: (id: number) => `/api/threats/${id}/share`,
  },
  
  // Analytics
  analytics: {
    threats: '/api/analytics/threats',
    fraudGraph: '/api/analytics/fraud-graph',
    transactions: '/api/analytics/transactions',
    dashboardStats: '/api/analytics/dashboard-stats',
  },
  
  // Mandates
  mandates: {
    list: '/api/mandates',
    create: '/api/mandates',
    get: (id: number) => `/api/mandates/${id}`,
    update: (id: number) => `/api/mandates/${id}`,
    delete: (id: number) => `/api/mandates/${id}`,
    toggle: (id: number) => `/api/mandates/${id}/toggle`,
  },
  
  // Vendors
  vendors: {
    list: '/api/vendors',
    create: '/api/vendors',
    get: (id: number) => `/api/vendors/${id}`,
    update: (id: number) => `/api/vendors/${id}`,
    invoices: (id: number) => `/api/vendors/${id}/invoices`,
  },
};
```

## API Service Layer

```typescript
// src/services/apiService.ts
import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
```

## Feature-Specific Services

### Invoice Service

```typescript
// src/services/invoiceService.ts
import apiClient from './apiService';
import { API_ENDPOINTS } from '../config/api';

export interface InvoiceUploadResponse {
  id: number;
  invoice_number: string;
  amount: number;
  status: string;
  confidence_score: number;
  fraud_score: number;
  decision: 'approve' | 'hold' | 'block';
  decision_reason: string;
  verification_details: any;
  fraud_indicators: string[];
  recommendation: string;
}

export const invoiceService = {
  async uploadInvoice(file: File, vendorId?: number, vendorName?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (vendorId) formData.append('vendor_id', vendorId.toString());
    if (vendorName) formData.append('vendor_name', vendorName);
    
    const response = await apiClient.post<InvoiceUploadResponse>(
      API_ENDPOINTS.invoices.upload,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  async listInvoices(params?: { status?: string; vendor_id?: number; skip?: number; limit?: number }) {
    const response = await apiClient.get(API_ENDPOINTS.invoices.list, { params });
    return response.data;
  },

  async getInvoice(id: number) {
    const response = await apiClient.get(API_ENDPOINTS.invoices.get(id));
    return response.data;
  },

  async reanalyzeInvoice(id: number) {
    const response = await apiClient.post(API_ENDPOINTS.invoices.reanalyze(id));
    return response.data;
  },
};
```

### Treasury Service

```typescript
// src/services/treasuryService.ts
import apiClient from './apiService';
import { API_ENDPOINTS } from '../config/api';

export interface TreasuryOverview {
  wallet_address: string;
  balance: number;
  total_paid: number;
  total_held: number;
  total_blocked: number;
  risk_prevented: number;
  pending_invoices: number;
  approved_invoices: number;
}

export const treasuryService = {
  async getOverview() {
    const response = await apiClient.get<TreasuryOverview>(
      API_ENDPOINTS.treasury.overview
    );
    return response.data;
  },

  async payInvoice(invoiceId: number, force: boolean = false) {
    const response = await apiClient.post(
      API_ENDPOINTS.treasury.pay(invoiceId),
      null,
      { params: { force } }
    );
    return response.data;
  },

  async triggerAutoPay() {
    const response = await apiClient.post(API_ENDPOINTS.treasury.autoPay);
    return response.data;
  },

  async getTransactions(params?: { skip?: number; limit?: number }) {
    const response = await apiClient.get(
      API_ENDPOINTS.treasury.transactions,
      { params }
    );
    return response.data;
  },

  async getBalance() {
    const response = await apiClient.get(API_ENDPOINTS.treasury.balance);
    return response.data;
  },
};
```

### Analytics Service

```typescript
// src/services/analyticsService.ts
import apiClient from './apiService';
import { API_ENDPOINTS } from '../config/api';

export const analyticsService = {
  async getThreatAnalytics() {
    const response = await apiClient.get(API_ENDPOINTS.analytics.threats);
    return response.data;
  },

  async getFraudGraph() {
    const response = await apiClient.get(API_ENDPOINTS.analytics.fraudGraph);
    return response.data;
  },

  async getTransactionHistory(params?: { status?: string; skip?: number; limit?: number }) {
    const response = await apiClient.get(
      API_ENDPOINTS.analytics.transactions,
      { params }
    );
    return response.data;
  },

  async getDashboardStats() {
    const response = await apiClient.get(API_ENDPOINTS.analytics.dashboardStats);
    return response.data;
  },
};
```

## React Hooks for Data Fetching

```typescript
// src/hooks/useInvoiceUpload.ts
import { useState } from 'react';
import { invoiceService } from '../services/invoiceService';

export function useInvoiceUpload() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const uploadInvoice = async (file: File, vendorId?: number, vendorName?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await invoiceService.uploadInvoice(file, vendorId, vendorName);
      setResult(data);
      return data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Upload failed';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { uploadInvoice, loading, error, result };
}
```

```typescript
// src/hooks/useTreasuryOverview.ts
import { useState, useEffect } from 'react';
import { treasuryService, TreasuryOverview } from '../services/treasuryService';

export function useTreasuryOverview() {
  const [data, setData] = useState<TreasuryOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const overview = await treasuryService.getOverview();
      setData(overview);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  return { data, loading, error, refetch: fetchOverview };
}
```

## Component Integration Examples

### Invoice Upload Component

```typescript
// src/components/InvoiceUpload.tsx
import { useInvoiceUpload } from '../hooks/useInvoiceUpload';

export function InvoiceUpload() {
  const { uploadInvoice, loading, error, result } = useInvoiceUpload();

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const data = await uploadInvoice(file);
      console.log('Upload successful:', data);
      
      // Display results to user
      if (data.decision === 'block') {
        alert(`Invoice BLOCKED: ${data.decision_reason}`);
      } else if (data.decision === 'approve') {
        alert(`Invoice APPROVED: ${data.decision_reason}`);
      } else {
        alert(`Invoice HELD for review: ${data.decision_reason}`);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  return (
    <div>
      <input type="file" accept=".pdf,.json" onChange={handleFileUpload} disabled={loading} />
      {loading && <p>Uploading and analyzing...</p>}
      {error && <p className="error">{error}</p>}
      {result && (
        <div>
          <h3>Analysis Results</h3>
          <p>Confidence Score: {(result.confidence_score * 100).toFixed(1)}%</p>
          <p>Fraud Score: {(result.fraud_score * 100).toFixed(1)}%</p>
          <p>Decision: {result.decision}</p>
          <p>Reason: {result.decision_reason}</p>
        </div>
      )}
    </div>
  );
}
```

### Treasury Dashboard Component

```typescript
// src/components/TreasuryDashboard.tsx
import { useTreasuryOverview } from '../hooks/useTreasuryOverview';

export function TreasuryDashboard() {
  const { data, loading, error } = useTreasuryOverview();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="treasury-dashboard">
      <h2>Treasury Overview</h2>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Balance</h3>
          <p>${data.balance.toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <h3>Total Paid</h3>
          <p>${data.total_paid.toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <h3>Risk Prevented</h3>
          <p>${data.risk_prevented.toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <h3>Total Blocked</h3>
          <p>${data.total_blocked.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
```

## Environment Variables

Add to your `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## CORS Configuration

The backend is already configured to accept requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative dev server)

To add more origins, update `backend/app/config.py`:

```python
ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://your-domain.com"
```

## Error Handling Best Practices

```typescript
// src/utils/errorHandler.ts
export function handleApiError(error: any): string {
  if (error.response) {
    // Server responded with error
    return error.response.data?.detail || error.response.data?.message || 'Server error';
  } else if (error.request) {
    // Request made but no response
    return 'No response from server. Please check your connection.';
  } else {
    // Request setup error
    return error.message || 'An error occurred';
  }
}
```

## WebSocket Support (Future)

For real-time updates:

```typescript
// src/services/websocketService.ts
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time invoice updates
};
```

## Testing

```typescript
// src/services/__tests__/invoiceService.test.ts
import { invoiceService } from '../invoiceService';

jest.mock('./apiService');

describe('Invoice Service', () => {
  it('should upload invoice', async () => {
    const file = new File(['test'], 'invoice.pdf');
    const result = await invoiceService.uploadInvoice(file);
    expect(result).toBeDefined();
  });
});
```

## Summary

The backend provides a complete RESTful API for all ShieldNet features. Key integration points:

1. **Invoice Processing**: Upload → Parse → Verify → Score → Decide
2. **Treasury Management**: View balance, execute payments, auto-pay
3. **Threat Intelligence**: Query threats, report new threats, view analytics
4. **Analytics**: Dashboard stats, fraud graph, transaction history
5. **Governance**: Manage mandates, vendors, POs, contracts

All endpoints return JSON responses with consistent error handling.
