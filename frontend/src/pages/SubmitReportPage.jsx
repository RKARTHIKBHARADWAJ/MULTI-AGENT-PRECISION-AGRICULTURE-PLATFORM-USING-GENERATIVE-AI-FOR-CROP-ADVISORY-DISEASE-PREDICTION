import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function SubmitReportPage() {
  const navigate = useNavigate();
  const [fields, setFields] = useState([]);
  const [form, setForm] = useState({
    crop: "wheat",
    growth_stage: "flowering",
    latitude: "12.97",
    longitude: "77.59",
    field_id: "",
    moisture_pct: "18.5",
    ph: "5.6",
    nitrogen_ppm: "30",
    phosphorus_ppm: "20",
    potassium_ppm: "140",
  });
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listFields().then(setFields).catch(() => {});
  }, []);

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      if (value !== "") {
        formData.append(key, value);
      }
    });
    if (image) {
      formData.append("image", image);
    }

    try {
      const report = await api.runReportWithImage(formData);
      navigate(`/reports/${report.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Submit Field Report</h2>
      <p className="muted">
        Runs the full multi-agent pipeline: weather, soil, disease, advisory, and decisions.
      </p>
      {error && <p className="error">{error}</p>}

      <form className="card form-card wide" onSubmit={handleSubmit}>
        <div className="form-grid">
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
          <label>
            Field (optional)
            <select value={form.field_id} onChange={(e) => updateField("field_id", e.target.value)}>
              <option value="">None</option>
              {fields.map((field) => (
                <option key={field.id} value={field.id}>
                  {field.name} ({field.crop})
                </option>
              ))}
            </select>
          </label>
          <label>
            Leaf image (optional)
            <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} />
          </label>
        </div>

        <h3>Soil readings</h3>
        <div className="form-grid">
          <label>
            Moisture %
            <input value={form.moisture_pct} onChange={(e) => updateField("moisture_pct", e.target.value)} />
          </label>
          <label>
            pH
            <input value={form.ph} onChange={(e) => updateField("ph", e.target.value)} />
          </label>
          <label>
            Nitrogen ppm
            <input value={form.nitrogen_ppm} onChange={(e) => updateField("nitrogen_ppm", e.target.value)} />
          </label>
          <label>
            Phosphorus ppm
            <input value={form.phosphorus_ppm} onChange={(e) => updateField("phosphorus_ppm", e.target.value)} />
          </label>
          <label>
            Potassium ppm
            <input value={form.potassium_ppm} onChange={(e) => updateField("potassium_ppm", e.target.value)} />
          </label>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Running pipeline..." : "Run Multi-Agent Report"}
        </button>
      </form>
    </div>
  );
}
