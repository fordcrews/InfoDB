import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { createAgency, deleteAgency, fetchAgencies } from "../api/client";
import AdminGate from "../components/AdminGate";
import Layout from "../components/Layout";

export default function AgenciesPage() {
  const queryClient = useQueryClient();
  const agenciesQuery = useQuery({ queryKey: ["agencies"], queryFn: fetchAgencies });
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const createMutation = useMutation({
    mutationFn: () => createAgency({ name, description: description || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agencies"] });
      setName("");
      setDescription("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAgency,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agencies"] }),
  });

  function handleCreate(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  return (
    <Layout>
      <header className="page-header">
        <h2>Agencies</h2>
      </header>

      <AdminGate>
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Add agency</h3>
          <form onSubmit={handleCreate} className="toolbar">
            <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <input
              placeholder="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
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
              <th>Description</th>
              <th>Subnets</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {agenciesQuery.data?.map((agency) => (
              <tr key={agency.id}>
                <td>{agency.name}</td>
                <td>{agency.description ?? "—"}</td>
                <td>{agency.subnet_count}</td>
                <td>
                  <AdminGate>
                    <button
                      className="btn-danger"
                      onClick={() => deleteMutation.mutate(agency.id)}
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