const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type User = {
  id: number;
  email: string;
  display_name: string;
  role: string;
};

export type Asset = {
  id: number;
  mac_address: string;
  ip_address: string;
  hostname: string | null;
  os_name: string | null;
  sys_descr: string | null;
  device_type: string | null;
  subnet: { id: number; cidr: string } | null;
  first_seen: string;
  last_seen: string;
};

export type AssetListResponse = {
  items: Asset[];
  total: number;
  page: number;
  page_size: number;
};

export type AgencyOsCount = {
  agency_name: string;
  os_name: string;
  count: number;
};

export type DashboardStats = {
  total_assets: number;
  assets_seen_24h: number;
  router_count: number;
  subnet_count: number;
  last_discovery_at: string | null;
  last_discovery_status: string | null;
  agency_os_counts: AgencyOsCount[];
};

export type Agency = {
  id: number;
  name: string;
  description: string | null;
  subnet_count: number;
};

export type Subnet = {
  id: number;
  cidr: string;
  description: string | null;
  agency_id: number | null;
  agency: { id: number; name: string } | null;
  asset_count: number;
};

export type SnmpProfile = {
  id: number;
  name: string;
  version: string;
  community: string | null;
  username: string | null;
  auth_protocol: string | null;
  priv_protocol: string | null;
  created_at: string;
  router_count: number;
};

export type Router = {
  id: number;
  name: string;
  ip_address: string;
  description: string | null;
  snmp_profile_id: number | null;
  is_active: boolean;
  created_at: string;
  snmp_profile: { id: number; name: string } | null;
};

export type DiscoveryRun = {
  id: number;
  run_type: string;
  status: string;
  router_id: number | null;
  router_name: string | null;
  assets_found: number;
  assets_updated: number;
  assets_new: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

function getToken(): string | null {
  return localStorage.getItem("infodb_token");
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem("infodb_token", token);
  } else {
    localStorage.removeItem("infodb_token");
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = await response.text();
    try {
      const parsed = JSON.parse(detail) as { detail?: string };
      detail = parsed.detail ?? detail;
    } catch {
      // keep raw text
    }
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!response.ok) {
    throw new Error("Invalid email or password");
  }

  return response.json() as Promise<TokenResponse>;
}

export function fetchMe(): Promise<User> {
  return apiFetch<User>("/api/v1/auth/me");
}

export function fetchStats(): Promise<DashboardStats> {
  return apiFetch<DashboardStats>("/api/v1/assets/stats");
}

export function fetchAssets(
  page = 1,
  search = "",
  subnetId?: number,
): Promise<AssetListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: "25" });
  if (search) params.set("search", search);
  if (subnetId) params.set("subnet_id", String(subnetId));
  return apiFetch<AssetListResponse>(`/api/v1/assets?${params}`);
}

export function fetchAsset(id: number): Promise<Asset> {
  return apiFetch<Asset>(`/api/v1/assets/${id}`);
}

export function updateAsset(
  id: number,
  data: Partial<Pick<Asset, "hostname" | "os_name" | "sys_descr" | "device_type">> & {
    subnet_id?: number | null;
  },
): Promise<Asset> {
  return apiFetch<Asset>(`/api/v1/assets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function fetchAgencies(): Promise<Agency[]> {
  return apiFetch<Agency[]>("/api/v1/agencies");
}

export function createAgency(data: { name: string; description?: string }): Promise<Agency> {
  return apiFetch<Agency>("/api/v1/agencies", { method: "POST", body: JSON.stringify(data) });
}

export function updateAgency(
  id: number,
  data: Partial<{ name: string; description: string | null }>,
): Promise<Agency> {
  return apiFetch<Agency>(`/api/v1/agencies/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteAgency(id: number): Promise<void> {
  return apiFetch<void>(`/api/v1/agencies/${id}`, { method: "DELETE" });
}

export function fetchSubnets(): Promise<Subnet[]> {
  return apiFetch<Subnet[]>("/api/v1/subnets");
}

export function createSubnet(data: {
  cidr: string;
  description?: string;
  agency_id?: number | null;
}): Promise<Subnet> {
  return apiFetch<Subnet>("/api/v1/subnets", { method: "POST", body: JSON.stringify(data) });
}

export function updateSubnet(
  id: number,
  data: Partial<{ cidr: string; description: string | null; agency_id: number | null }>,
): Promise<Subnet> {
  return apiFetch<Subnet>(`/api/v1/subnets/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteSubnet(id: number): Promise<void> {
  return apiFetch<void>(`/api/v1/subnets/${id}`, { method: "DELETE" });
}

export function fetchRouters(): Promise<Router[]> {
  return apiFetch<Router[]>("/api/v1/routers");
}

export function createRouter(data: {
  name: string;
  ip_address: string;
  description?: string;
  snmp_profile_id?: number | null;
  is_active?: boolean;
}): Promise<Router> {
  return apiFetch<Router>("/api/v1/routers", { method: "POST", body: JSON.stringify(data) });
}

export function updateRouter(
  id: number,
  data: Partial<{
    name: string;
    ip_address: string;
    description: string | null;
    snmp_profile_id: number | null;
    is_active: boolean;
  }>,
): Promise<Router> {
  return apiFetch<Router>(`/api/v1/routers/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteRouter(id: number): Promise<void> {
  return apiFetch<void>(`/api/v1/routers/${id}`, { method: "DELETE" });
}

export function fetchSnmpProfiles(): Promise<SnmpProfile[]> {
  return apiFetch<SnmpProfile[]>("/api/v1/snmp-profiles");
}

export function createSnmpProfile(data: Record<string, unknown>): Promise<SnmpProfile> {
  return apiFetch<SnmpProfile>("/api/v1/snmp-profiles", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateSnmpProfile(id: number, data: Record<string, unknown>): Promise<SnmpProfile> {
  return apiFetch<SnmpProfile>(`/api/v1/snmp-profiles/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteSnmpProfile(id: number): Promise<void> {
  return apiFetch<void>(`/api/v1/snmp-profiles/${id}`, { method: "DELETE" });
}

export function fetchDiscoveryRuns(page = 1): Promise<{ items: DiscoveryRun[]; total: number }> {
  const params = new URLSearchParams({ page: String(page), page_size: "25" });
  return apiFetch(`/api/v1/discovery/runs?${params}`);
}

export function triggerDiscovery(routerId?: number): Promise<DiscoveryRun[]> {
  return apiFetch<DiscoveryRun[]>("/api/v1/discovery/runs", {
    method: "POST",
    body: JSON.stringify({ router_id: routerId ?? null }),
  });
}

export function testRouterSnmp(routerId: number): Promise<{ success: boolean; sys_descr?: string; message?: string; error?: string }> {
  return apiFetch(`/api/v1/routers/${routerId}/test`, {
    method: "POST",
  });
}