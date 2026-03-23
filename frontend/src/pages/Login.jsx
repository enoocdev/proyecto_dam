// Pagina de inicio de sesion con formulario de usuario y contrasena
// Obtiene los tokens JWT y los permisos del usuario al autenticarse
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { ACCESS_TOKEN, REFRESH_TOKEN , USER_PERMISSIONS} from "../constants";
import { setUserClassrooms } from '../stores/userClassroomsStore';

import { TextField, Button, Alert, CircularProgress, Typography } from "@mui/material";
import "../styles/Login.css";

function Login() {
    const [credentials, setCredentials] = useState({ username: "", password: "" });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const navigate = useNavigate();

    const handleChange = (e) => {
        setCredentials({ ...credentials, [e.target.name]: e.target.value });
        if (error) setError(null);
    };

    const getToken = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const res = await api.post("/token/", credentials);
            localStorage.setItem(ACCESS_TOKEN, res.data.access);
            localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
            const userData = {
                is_superuser: res.data.is_superuser,
                is_staff: res.data.is_staff,
                permissions: res.data.permissions,
                
            }
            localStorage.setItem(USER_PERMISSIONS, JSON.stringify(userData))
            setUserClassrooms(res.data.classrooms || []);
            navigate("/");
        } catch (err) {
            if (err.response && err.response.status === 401) {
                setError("Credenciales incorrectas.");
            } else {
                setError("Error de conexión.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">

                <Typography variant="h5" style={{ color: 'var(--text-primary)', marginBottom: '10px' }}>
                    Bienvenido
                </Typography>

                <Typography variant="body2" style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
                    Inicia sesión para continuar
                </Typography>

                {error && (
                    <Alert severity="error" style={{ width: '100%', marginBottom: '20px' }}>
                        {error}
                    </Alert>
                )}

                <form onSubmit={getToken} style={{ width: '100%' }}>
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        label="Usuario"
                        name="username"
                        value={credentials.username}
                        onChange={handleChange}
                        autoComplete="off"
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        label="Contraseña"
                        type="password"
                        name="password"
                        value={credentials.password}
                        onChange={handleChange}
                    />

                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        disabled={loading}
                        style={{
                            marginTop: '20px',
                            height: '45px',
                            backgroundColor: 'var(--accent-color)',
                            color: 'var(--text-on-accent)'
                        }}
                    >
                        {loading ? <CircularProgress size={24} color="inherit" /> : "Iniciar Sesión"}
                    </Button>
                </form>
            </div>
        </div>
    );
}

export default Login;