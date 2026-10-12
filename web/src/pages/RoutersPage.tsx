import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, Fragment, useState } from "react";
import { createRouter, deleteRouter, fetchRouters, fetchSnmpProfiles, testRouterSnmp } from "../api/client";
import AdminGate from "../components/AdminGate";
import Layout from "../components/Layout";

export default function RoutersPage() {
  const queryClient = useQueryClient();
  const routersQuery = useQuery({ queryKey: ["routers"], queryFn: fetchRouters });
  const profilesQuery = useQuery({ queryKey: ["snmp-profiles"], queryFn: fetchSnmpProfiles });

  const [name, setName] = useState("");
  const [ipAddress, setIpAddress] = useState("");
  const [description, setDescription] = useState("");
  const [profileId, setProfileId] = useState("");

  const createMutation = useMutation({
    mutationFn: () =>
      createRouter({
        name,
        ip_address: ipAddress,
        description: description || undefined,
        snmp_profile_id: profileId ? Number(profileId) : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["routers"] });
      setName("");
      setIpAddress("");
      setDescription("");
      setProfileId("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRouter,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["routers"] }),
  });

  const [testResults, setTestResults] = useState<Record<number, any>>({});

  const testMutation = useMutation({
    mutationFn: (routerId: number) => testRouterSnmp(routerId),
    onSuccess: (data, routerId) => {
      setTestResults((prev) => ({ ...prev, [routerId]: data }));
    },
  });

  function handleCreate(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  function handleTest(routerId: number) {
    testMutation.mutate(routerId);
  }

  return (
    <Layout>
      <header className="page-header">
        <h2>Routers</h2>
      </header>

      <AdminGate>
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Add router</h3>
          <form onSubmit={handleCreate} className="toolbar">
            <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <input
              placeholder="IP address"
              value={ipAddress}
              onChange={(e) => setIpAddress(e.target.value)}
              required
            />
            <input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
            <select value={profileId} onChange={(e) => setProfileId(e.target.value)}>
              <option value="">No SNMP profile</option>
              {profilesQuery.data?.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              Add
            </button>
          </form>
          {createMutation.error && <p className="error">{String(createMutation.error.message)}</p>}
        </div>
      </AdminGate>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>IP</th>
              <th>SNMP Profile</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {routersQuery.data?.map((router) => (
              <Fragment key={router.id}>
                <tr>
                  <td>{router.name}</td>
                  <td>{router.ip_address}</td>
                  <td>{router.snmp_profile?.name ?? "—"}</td>
                  <td>{router.is_active ? "Yes" : "No"}</td>
                  <td>
                    <AdminGate>
                      <button
                        className="btn-secondary"
                        onClick={() => handleTest(router.id)}
                        disabled={testMutation.isPending}
                        style={{ marginRight: "0.5rem" }}
                      >
                        Test SNMP
                      </button>
                      <button
                        className="btn-danger"
                        onClick={() => deleteMutation.mutate(router.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Delete
                      </button>
                    </AdminGate>
                  </td>
                </tr>
                {testResults[router.id] && (
                  <tr>
                    <td colSpan={5} style={{ paddingLeft: "1rem", background: "#f8f9fc" }}>
                      {testResults[router.id].success ? (
                        <span className="success">
                          ✓ {testResults[router.id].message} — {testResults[router.id].sys_descr}
                        </span>
                      ) : (
                        <span className="error">
                          ✗ {testResults[router.id].error || "Test failed"}
                        </span>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}