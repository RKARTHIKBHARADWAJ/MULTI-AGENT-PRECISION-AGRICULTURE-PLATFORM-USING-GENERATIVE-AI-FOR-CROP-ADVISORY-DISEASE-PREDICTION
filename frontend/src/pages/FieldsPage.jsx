import { useEffect, useState } from "react";
import { api } from "../api";

export default function FieldsPage() {
  const [fields, setFields] = useState([]);
  const [form, setForm] = useState({
    name: "",
    crop: "wheat",
    growth_stage: "flowering",
    latitude: "12.97",
    longitude: "77.59",
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadFields() {
    const data = await api.listFields();
    setFields(data);
  }

  useEffect(() => {
    loadFields().catch((err) => setError(err.message));
  }, []);

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await api.createField({
        ...form,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
      });
      setMessage("Field saved.");
      setForm({ ...form, name: "" });
      await loadFields();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <h2>My Fields</h2>
      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <div className="card-grid">
        <form className="card form-card" onSubmit={handleSubmit}>
          <h3>Add Field</h3>
          <label>
            Name
            <input value={form.name} onChange={(e) => updateField("name", e.target.value)} required />
          </label>
          <label>
            Crop
            <input value={form.crop} onChange={(e) => updateField("crop", e.target.value)} required />
          </label>
          <label>
            Growth stage
            <input value={form.growth_stage} onChange={(e) => updateField("growth_stage", e.target.value)} />
          </label>
          <label>
            Latitude
            <input value={form.latitude} onChange={(e) => updateField("latitude", e.target.value)} required />
          </label>
          <label>
            Longitude
            <input value={form.longitude} onChange={(e) => updateField("longitude", e.target.value)} required />
          </label>
          <button type="submit">Save Field</button>
        </form>

        <div className="card">
          <h3>Saved Fields</h3>
          {fields.length === 0 ? (
            <p>No fields yet.</p>
          ) : (
            <ul>
              {fields.map((field) => (
                <li key={field.id}>
                  <strong>{field.name}</strong> — {field.crop} at ({field.latitude}, {field.longitude})
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
