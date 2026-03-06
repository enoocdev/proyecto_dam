import React from 'react';
import { Box, Paper, Typography, Button } from '@mui/material';
import LockPersonIcon from '@mui/icons-material/LockPerson';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useNavigate } from 'react-router-dom'; // Asumo que usas react-router

const RestrictedAccess = () => {
    const navigate = useNavigate();

    const goBack = () => {
        // Intenta ir atrás en el historial, si no hay, va al inicio
        if (window.history.state && window.history.state.idx > 0) {
            navigate(-1);
        } else {
            navigate('/'); // Cambia '/' por tu ruta principal si es diferente
        }
    };

    return (
        <Box
            sx={{
                // Centra el contenido vertical y horizontalmente en la pantalla
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '70vh', // Altura mínima para que quede centrado bonito
                padding: 3,
                background: 'transparent' // Deja ver el fondo de tu app (#121212)
            }}
        >
            <Paper
                elevation={10}
                sx={{
                    bgcolor: 'var(--bg-card)',
                    border: '2px solid var(--accent-border-strong)',
                    borderRadius: '24px',
                    p: { xs: 4, md: 6 },
                    textAlign: 'center',
                    maxWidth: 550,
                    width: '100%',
                    
                    boxShadow: '0 15px 40px var(--shadow-glow)',

                    animation: 'fadeInUp 0.5s ease-out',
                    '@keyframes fadeInUp': {
                        '0%': { opacity: 0, transform: 'translateY(30px)' },
                        '100%': { opacity: 1, transform: 'translateY(0)' }
                    },

                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center'
                }}
            >
                {/* --- ICONO DEL CANDADO --- */}
                <Box
                    sx={{
                        mb: 3,
                        p: 3,
                        borderRadius: '50%',
                        background: 'var(--accent-bg)',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        animation: 'pulse 2s infinite ease-in-out',
                        '@keyframes pulse': {
                            '0%': { boxShadow: '0 0 0 0 rgba(139, 92, 246, 0.4)' },
                            '70%': { boxShadow: '0 0 0 20px rgba(139, 92, 246, 0)' },
                            '100%': { boxShadow: '0 0 0 0 rgba(139, 92, 246, 0)' }
                        }
                    }}
                >
                    <LockPersonIcon
                        sx={{
                            fontSize: 70,
                            color: 'var(--accent-color)',
                        }}
                    />
                </Box>

                {/* --- TÍTULO --- */}
                <Typography 
                    variant="h4" 
                    sx={{ 
                        fontWeight: '900',
                        color: 'var(--text-primary)', 
                        mb: 2,
                        letterSpacing: '1px'
                    }}
                >
                    Zona Restringida
                </Typography>

                {/* --- DESCRIPCIÓN --- */}
                <Typography 
                    variant="body1" 
                    sx={{ 
                        color: 'var(--text-secondary)', // Gris claro para el texto secundario
                        fontSize: '1.1rem', 
                        lineHeight: 1.6,
                        mb: 4,
                        maxWidth: '90%'
                    }}
                >
                    Lo sentimos, tu cuenta no tiene los 
                    <Box component="span" sx={{ color: 'var(--accent-medium)', fontWeight: 'bold' }}> permisos necesarios </Box> 
                    para acceder a esta sección.
                    Si crees que se trata de un error, contacta con un administrador.
                </Typography>

                {/* --- BOTÓN DE VOLVER --- */}
                <Button
                    variant="outlined"
                    startIcon={<ArrowBackIcon />}
                    onClick={goBack}
                    sx={{
                        color: 'var(--text-primary)',
                        borderColor: 'var(--accent-color)',
                        borderRadius: '12px',
                        padding: '10px 24px',
                        textTransform: 'none',
                        fontSize: '1rem',
                        fontWeight: '600',
                        borderWidth: '2px',
                        '&:hover': {
                            borderColor: 'var(--accent-hover)',
                            background: 'var(--accent-bg)',
                            borderWidth: '2px'
                        }
                    }}
                >
                    Volver atrás
                </Button>
            </Paper>
        </Box>
    );
};

export default RestrictedAccess;