import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { createSubnet, deleteSubnet, fetchAgencies, fetchSubnets } from "../api/client";
import AdminGate from "../components/AdminGate";
import Layout from "../components/Layout";

export default function SubnetsPage() {
  const queryClient = useQueryClient();
  const subnetsQuery = useQuery({ queryKey: ["subnets"], queryFn: fetchSubnets });
  const agenciesQuery = useQuery({ queryKey: ["agencies"], queryFn: fetchAgencies });

  const [cidr, setCidr] = useState("");
  const [description, setDescription] = useState("");
  const [agencyId, setAgencyId] = useState("");

  const createMutation = useMutation({
    mutationFn: () =>
      createSubnet({
        cidr,
        description: description || undefined,
        agency_id: agencyId ? Number(agencyId) : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subnets"] });
      setCidr("");
      setDescription("");
      setAgencyId("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSubnet,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["subnets"] }),
  });

  function handleCreate(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  return (
    <Layout>
      <header className="page-header">
        <h2>Subnets</h2>
      </header>

      <AdminGate>
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Add subnet</h3>
          <form onSubmit={handleCreate} className="toolbar">
            <input placeholder="CIDR (10.0.0.0/24)" value={cidr} onChange={(e) => setCidr(e.target.value)} required />
            <input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
            <select value={agencyId} onChange={(e) => setAgencyId(e.target.value)}>
              <option value="">No agency</option>
              {agenciesQuery.data?.map((agency) => (
                <option key={agency.id} value={agency.id}>
                  {agency.name}
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
              <th>CIDR</th>
              <th>Description</th>
              <th>Agency</th>
              <th>Assets</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {subnetsQuery.data?.map((subnet) => (
              <tr key={subnet.id}>
                <td>{subnet.cidr}</td>
                <td>{subnet.description ?? "—"}</td>
                <td>{subnet.agency?.name ?? "—"}</td>
                <td>{subnet.asset_count}</td>
                <td>
                  <AdminGate>
                    <button
                      className="btn-danger"
                      onClick={() => deleteMutation.mutate(subnet.id)}
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