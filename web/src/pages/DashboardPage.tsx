import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAssets, fetchStats, fetchSubnets } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";

export default function DashboardPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [subnetId, setSubnetId] = useState<number | undefined>();

  const statsQuery = useQuery({ queryKey: ["stats"], queryFn: fetchStats });
  const subnetsQuery = useQuery({ queryKey: ["subnets"], queryFn: fetchSubnets });
  const assetsQuery = useQuery({
    queryKey: ["assets", page, search, subnetId],
    queryFn: () => fetchAssets(page, search, subnetId),
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  }

  const stats = statsQuery.data;
  const assets = assetsQuery.data;

  return (
    <Layout>
      <header className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p className="muted">Welcome, {user?.display_name}</p>
        </div>
        <Link to="/discovery" className="btn-primary">
          Run Discovery
        </Link>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total assets</h3>
          <p>{stats?.total_assets ?? "—"}</p>
        </div>
        <div className="stat-card">
          <h3>Seen (24h)</h3>
          <p>{stats?.assets_seen_24h ?? "—"}</p>
        </div>
        <div className="stat-card">
          <h3>Routers</h3>
          <p>{stats?.router_count ?? "—"}</p>
        </div>
        <div className="stat-card">
          <h3>Subnets</h3>
          <p>{stats?.subnet_count ?? "—"}</p>
        </div>
      </div>

      {stats?.last_discovery_at && (
        <div className="card info-banner">
          Last discovery: {new Date(stats.last_discovery_at).toLocaleString()} —{" "}
          <span className={`status-pill status-${stats.last_discovery_status}`}>
            {stats.last_discovery_status}
          </span>
        </div>
      )}

      {stats && stats.agency_os_counts.length > 0 && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Assets by agency & OS</h3>
          <table>
            <thead>
              <tr>
                <th>Agency</th>
                <th>OS</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {stats.agency_os_counts.map((row, i) => (
                <tr key={`${row.agency_name}-${row.os_name}-${i}`}>
                  <td>{row.agency_name}</td>
                  <td>{row.os_name}</td>
                  <td>{row.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSearch} className="toolbar">
          <input
            placeholder="Search MAC, IP, hostname..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <select
            value={subnetId ?? ""}
            onChange={(e) => {
              setPage(1);
              setSubnetId(e.target.value ? Number(e.target.value) : undefined);
            }}
          >
            <option value="">All subnets</option>
            {subnetsQuery.data?.map((subnet) => (
              <option key={subnet.id} value={subnet.id}>
                {subnet.cidr}
              </option>
            ))}
          </select>
          <button type="submit" className="btn-primary">
            Search
          </button>
        </form>

        {assetsQuery.isLoading && <p>Loading assets...</p>}
        {assetsQuery.error && <p className="error">Failed to load assets</p>}

        {assets && (
          <>
            <table>
              <thead>
                <tr>
                  <th>IP</th>
                  <th>MAC</th>
                  <th>Hostname</th>
                  <th>OS</th>
                  <th>Subnet</th>
                  <th>Last seen</th>
                </tr>
              </thead>
              <tbody>
                {assets.items.map((asset) => (
                  <tr key={asset.id}>
                    <td>
                      <Link to={`/assets/${asset.id}`}>{asset.ip_address}</Link>
                    </td>
                    <td>{asset.mac_address}</td>
                    <td>{asset.hostname ?? "—"}</td>
                    <td>{asset.os_name ?? "—"}</td>
                    <td>{asset.subnet?.cidr ?? "—"}</td>
                    <td>{new Date(asset.last_seen).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="pagination">
              <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </button>
              <span>
                Page {assets.page} · {assets.total} total
              </span>
              <button
                className="btn-secondary"
                disabled={assets.items.length < assets.page_size}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}