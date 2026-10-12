import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchAsset, fetchSubnets, updateAsset } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import AdminGate from "../components/AdminGate";
import Layout from "../components/Layout";

export default function AssetDetailPage() {
  const { id } = useParams();
  const assetId = Number(id);
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const isAdmin = user?.role === "admin";

  const assetQuery = useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => fetchAsset(assetId),
    enabled: Number.isFinite(assetId),
  });

  const subnetsQuery = useQuery({ queryKey: ["subnets"], queryFn: fetchSubnets });

  const [hostname, setHostname] = useState("");
  const [osName, setOsName] = useState("");
  const [deviceType, setDeviceType] = useState("");
  const [sysDescr, setSysDescr] = useState("");
  const [subnetId, setSubnetId] = useState<string>("");

  useEffect(() => {
    if (assetQuery.data) {
      setHostname(assetQuery.data.hostname ?? "");
      setOsName(assetQuery.data.os_name ?? "");
      setDeviceType(assetQuery.data.device_type ?? "");
      setSysDescr(assetQuery.data.sys_descr ?? "");
      setSubnetId(assetQuery.data.subnet?.id ? String(assetQuery.data.subnet.id) : "");
    }
  }, [assetQuery.data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateAsset(assetId, {
        hostname: hostname || null,
        os_name: osName || null,
        device_type: deviceType || null,
        sys_descr: sysDescr || null,
        subnet_id: subnetId ? Number(subnetId) : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asset", assetId] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  function handleSave(event: FormEvent) {
    event.preventDefault();
    saveMutation.mutate();
  }

  const asset = assetQuery.data;

  return (
    <Layout>
      <header className="page-header">
        <div>
          <Link to="/" className="muted">
            ← Back to dashboard
          </Link>
          <h2>{asset?.ip_address ?? "Asset"}</h2>
        </div>
      </header>

      {assetQuery.isLoading && <p>Loading...</p>}
      {assetQuery.error && <p className="error">Asset not found</p>}

      {asset && (
        <div className="card">
          <dl className="detail-grid">
            <dt>MAC</dt>
            <dd>{asset.mac_address}</dd>
            <dt>First seen</dt>
            <dd>{new Date(asset.first_seen).toLocaleString()}</dd>
            <dt>Last seen</dt>
            <dd>{new Date(asset.last_seen).toLocaleString()}</dd>
            <dt>Subnet</dt>
            <dd>{asset.subnet?.cidr ?? "—"}</dd>
          </dl>

          {isAdmin ? (
            <AdminGate>
              <form onSubmit={handleSave} className="form-grid">
                <label>
                  Hostname
                  <input value={hostname} onChange={(e) => setHostname(e.target.value)} />
                </label>
                <label>
                  OS
                  <input value={osName} onChange={(e) => setOsName(e.target.value)} />
                </label>
                <label>
                  Device type
                  <input value={deviceType} onChange={(e) => setDeviceType(e.target.value)} />
                </label>
                <label>
                  Subnet
                  <select value={subnetId} onChange={(e) => setSubnetId(e.target.value)}>
                    <option value="">Unassigned</option>
                    {subnetsQuery.data?.map((subnet) => (
                      <option key={subnet.id} value={subnet.id}>
                        {subnet.cidr}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="full-width">
                  System description
                  <textarea
                    rows={4}
                    value={sysDescr}
                    onChange={(e) => setSysDescr(e.target.value)}
                  />
                </label>
                <div className="full-width">
                  <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
                    {saveMutation.isPending ? "Saving..." : "Save changes"}
                  </button>
                  {saveMutation.error && <p className="error">{String(saveMutation.error.message)}</p>}
                  {saveMutation.isSuccess && <p className="success">Saved.</p>}
                </div>
              </form>
            </AdminGate>
          ) : (
            <dl className="detail-grid">
              <dt>Hostname</dt>
              <dd>{asset.hostname ?? "—"}</dd>
              <dt>OS</dt>
              <dd>{asset.os_name ?? "—"}</dd>
              <dt>Device type</dt>
              <dd>{asset.device_type ?? "—"}</dd>
              <dt>Description</dt>
              <dd>{asset.sys_descr ?? "—"}</dd>
            </dl>
          )}
        </div>
      )}
    </Layout>
  );
}