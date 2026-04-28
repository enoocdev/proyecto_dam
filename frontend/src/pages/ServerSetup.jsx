// Pantalla de configuracion inicial del servidor
// Se muestra la primera vez que se abre la app 
// Permite al usuario indicar la IP/dominio donde tiene desplegado el backend
import { useState } from "react";
import { TextField, Button, Alert, CircularProgress, Typography } from "@mui/material";
import DnsIcon from "@mui/icons-material/Dns";
import { SERVER_URL } from "../constants";
import axios from "axios";
import "../styles/ServerSetup.css";

function ServerSetup({ onConfigured }) {
    const [url, setUrl] = useState("http://");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const normalize = (raw) => raw.replace(/\/+$/, ""); // quitar trailing slash

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        const base = normalize(url.trim());
        if (!base.startsWith("http://") && !base.startsWith("https://")) {
            setError("La URL debe empezar por http:// o https://");
            return;
        }

        setLoading(true);
        try {
            // Prueba de conectividad: intenta llegar al endpoint de token
            // Si responde (aunque sea 400/405) el servidor está accesible
            await axios.get(`${base}/token/`, { timeout: 5000 });
        } catch (err) {
            // 400 / 405 significa que el servidor responde → OK
            if (!err.response) {
                setLoading(false);
                setError("No se pudo conectar. Comprueba la IP/puerto y que el servidor esté activo.");
                return;
            }
        }

        localStorage.setItem(SERVER_URL, base);
        setLoading(false);
        onConfigured();
    };

    return (
        <div className="setup-container">
            <div className="setup-card">
                <DnsIcon className="setup-icon" />
                <Typography variant="h5" className="setup-title">
                    Configurar servidor
                </Typography>
                <Typography variant="body2" className="setup-subtitle">
                    Introduce la dirección del servidor donde está instalado Net Management.
                </Typography>

                <form onSubmit={handleSubmit} className="setup-form">
                    <TextField
                        label="URL del servidor"
                        placeholder="http://192.168.1.100:8000"
                        value={url}
                        onChange={(e) => { setUrl(e.target.value); setError(null); }}
                        fullWidth
                        required
                        autoFocus
                        disabled={loading}
                    />

                    {error && <Alert severity="error">{error}</Alert>}

                    <Button
                        type="submit"
                        variant="contained"
                        fullWidth
                        disabled={loading}
                        className="setup-button"
                    >
                        {loading ? <CircularProgress size={22} /> : "Conectar"}
                    </Button>
                </form>
            </div>
        </div>
    );
}

export default ServerSetup;
