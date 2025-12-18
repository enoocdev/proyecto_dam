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
                    // --- ESTILOS PRINCIPALES DE LA TARJETA ---
                    bgcolor: '#1e1e1e', // Fondo oscuro de tarjeta
                    border: '2px solid rgba(139, 92, 246, 0.3)', // Borde violeta sutil
                    borderRadius: '24px', // Bordes muy redondeados
                    p: { xs: 4, md: 6 }, // Padding interno generoso (más en pantallas grandes)
                    textAlign: 'center',
                    maxWidth: 550,
                    width: '100%',
                    
                    // Resplandor violeta suave
                    boxShadow: '0 15px 40px rgba(139, 92, 246, 0.15)',

                    // Animación de entrada suave
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
                        background: 'rgba(139, 92, 246, 0.1)', // Círculo de fondo violeta transparente
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        // Pequeña animación de pulso en el icono
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
                            color: '#8b5cf6', // Color violeta principal
                        }}
                    />
                </Box>

                {/* --- TÍTULO --- */}
                <Typography 
                    variant="h4" 
                    sx={{ 
                        fontWeight: '900', // Fuente extra gruesa
                        color: '#fff', 
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
                        color: '#a1a1aa', // Gris claro para el texto secundario
                        fontSize: '1.1rem', 
                        lineHeight: 1.6,
                        mb: 4,
                        maxWidth: '90%'
                    }}
                >
                    Lo sentimos, tu cuenta no tiene los 
                    <Box component="span" sx={{ color: '#a78bfa', fontWeight: 'bold' }}> permisos necesarios </Box> 
                    para acceder a esta sección.
                    Si crees que se trata de un error, contacta con un administrador.
                </Typography>

                {/* --- BOTÓN DE VOLVER --- */}
                <Button
                    variant="outlined"
                    startIcon={<ArrowBackIcon />}
                    onClick={goBack}
                    sx={{
                        color: '#fff',
                        borderColor: '#8b5cf6',
                        borderRadius: '12px',
                        padding: '10px 24px',
                        textTransform: 'none',
                        fontSize: '1rem',
                        fontWeight: '600',
                        borderWidth: '2px',
                        '&:hover': {
                            borderColor: '#7c3aed',
                            background: 'rgba(139, 92, 246, 0.15)',
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