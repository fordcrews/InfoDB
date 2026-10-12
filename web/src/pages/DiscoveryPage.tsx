import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchDiscoveryRuns, fetchRouters, triggerDiscovery } from "../api/client";
import AdminGate from "../components/AdminGate";
import Layout from "../components/Layout";

export default function DiscoveryPage() {
  const queryClient = useQueryClient();
  const runsQuery = useQuery({ queryKey: ["discovery-runs"], queryFn: () => fetchDiscoveryRuns() });
  const routersQuery = useQuery({ queryKey: ["routers"], queryFn: fetchRouters });

  const discoverMutation = useMutation({
    mutationFn: (routerId?: number) => triggerDiscovery(routerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["discovery-runs"] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  return (
    <Layout>
      <header className="page-header">
        <div>
          <h2>Discovery</h2>
          <p className="muted">SNMP ARP walks populate the asset inventory from configured routers.</p>
        </div>
      </header>

      <AdminGate>
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Run ARP discovery</h3>
          <div className="toolbar">
            <button
              className="btn-primary"
              onClick={() => discoverMutation.mutate(undefined)}
              disabled={discoverMutation.isPending}
            >
              {discoverMutation.isPending ? "Running..." : "All active routers"}
            </button>
            {routersQuery.data?.map((router) => (
              <button
                key={router.id}
                className="btn-secondary"
                onClick={() => discoverMutation.mutate(router.id)}
                disabled={discoverMutation.isPending || !router.is_active}
              >
                {router.name}
              </button>
            ))}
          </div>
          {discoverMutation.error && <p className="error">{String(discoverMutation.error.message)}</p>}
          {discoverMutation.isSuccess && <p className="success">Discovery run completed.</p>}
        </div>
      </AdminGate>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Run history</h3>
        {runsQuery.isLoading && <p>Loading...</p>}
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Router</th>
              <th>Status</th>
              <th>Found</th>
              <th>New</th>
              <th>Updated</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {runsQuery.data?.items.map((run) => (
              <tr key={run.id}>
                <td>{new Date(run.created_at).toLocaleString()}</td>
                <td>{run.router_name ?? "All"}</td>
                <td>
                  <span className={`status-pill status-${run.status}`}>{run.status}</span>
                </td>
                <td>{run.assets_found}</td>
                <td>{run.assets_new}</td>
                <td>{run.assets_updated}</td>
                <td className="error-cell">{run.error_message ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}