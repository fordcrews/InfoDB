import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { createSnmpProfile, deleteSnmpProfile, fetchSnmpProfiles } from "../api/client";
import AdminGate from "../components/AdminGate";
import Layout from "../components/Layout";

export default function SnmpProfilesPage() {
  const queryClient = useQueryClient();
  const profilesQuery = useQuery({ queryKey: ["snmp-profiles"], queryFn: fetchSnmpProfiles });

  const [name, setName] = useState("");
  const [version, setVersion] = useState("v2c");
  const [community, setCommunity] = useState("public");
  const [username, setUsername] = useState("");
  const [authProtocol, setAuthProtocol] = useState("SHA");
  const [authPassword, setAuthPassword] = useState("");
  const [privProtocol, setPrivProtocol] = useState("AES");
  const [privPassword, setPrivPassword] = useState("");

  const createMutation = useMutation({
    mutationFn: () =>
      createSnmpProfile({
        name,
        version,
        community: version === "v2c" ? community : null,
        username: version === "v3" ? username : null,
        auth_protocol: version === "v3" ? authProtocol : null,
        auth_password: version === "v3" ? authPassword : null,
        priv_protocol: version === "v3" ? privProtocol : null,
        priv_password: version === "v3" ? privPassword : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["snmp-profiles"] });
      setName("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSnmpProfile,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["snmp-profiles"] }),
  });

  function handleCreate(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  return (
    <Layout>
      <header className="page-header">
        <h2>SNMP Profiles</h2>
      </header>

      <AdminGate>
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Add profile</h3>
          <form onSubmit={handleCreate} className="form-grid">
            <label>
              Name
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              Version
              <select value={version} onChange={(e) => setVersion(e.target.value)}>
                <option value="v2c">v2c</option>
                <option value="v3">v3</option>
              </select>
            </label>
            {version === "v2c" ? (
              <label>
                Community
                <input value={community} onChange={(e) => setCommunity(e.target.value)} />
              </label>
            ) : (
              <>
                <label>
                  Username
                  <input value={username} onChange={(e) => setUsername(e.target.value)} />
                </label>
                <label>
                  Auth protocol
                  <select value={authProtocol} onChange={(e) => setAuthProtocol(e.target.value)}>
                    <option value="SHA">SHA</option>
                    <option value="MD5">MD5</option>
                  </select>
                </label>
                <label>
                  Auth password
                  <input type="password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} />
                </label>
                <label>
                  Priv protocol
                  <select value={privProtocol} onChange={(e) => setPrivProtocol(e.target.value)}>
                    <option value="AES">AES</option>
                    <option value="DES">DES</option>
                  </select>
                </label>
                <label>
                  Priv password
                  <input type="password" value={privPassword} onChange={(e) => setPrivPassword(e.target.value)} />
                </label>
              </>
            )}
            <div className="full-width">
              <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                Add profile
              </button>
              {createMutation.error && <p className="error">{String(createMutation.error.message)}</p>}
            </div>
          </form>
        </div>
      </AdminGate>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Version</th>
              <th>Community / User</th>
              <th>Routers</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {profilesQuery.data?.map((profile) => (
              <tr key={profile.id}>
                <td>{profile.name}</td>
                <td>{profile.version}</td>
                <td>{profile.community ?? profile.username ?? "—"}</td>
                <td>{profile.router_count}</td>
                <td>
                  <AdminGate>
                    <button
                      className="btn-danger"
                      onClick={() => deleteMutation.mutate(profile.id)}
                      disabled={deleteMutation.isPending}
                    >
                      Delete
                    </button>
                  </AdminGate>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}