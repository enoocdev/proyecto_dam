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

    // quita slashes finales y asegura que termina en /api/
    const normalize = (raw) => {
        let base = raw.trim().replace(/\/+$/, "");
        // Quitar /api al final
        base = base.replace(/\/api$/, "");
        return base + "/api/";
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        const raw = url.trim();
        if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
            setError("La URL debe empezar por http:// o https://");
            return;
        }

        const base = normalize(raw);
        setLoading(true);

        try {
            await axios.get(base, {
                timeout: 6000,
                validateStatus: () => true,
            });
            
            localStorage.setItem(SERVER_URL, base);
            setLoading(false);
            onConfigured();
        } catch (err) {
            setError("Servidor no encontrado. Comprueba la dirección e inténtalo de nuevo.");
            setLoading(false);
        }
    };

    return (
        <div className="setup-container">
            <div className="setup-card">
                <DnsIcon className="setup-icon" />
                <Typography variant="h5" className="setup-title">
                    Configurar servidor
                </Typography>
                <Typography variant="body2" className="setup-subtitle">
                    Introduce la direccion del servidor donde esta instalado Net Management.
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