// Pagina de gestion de dispositivos de red (switches y routers)
// Permite crear editar y eliminar dispositivos de red con CRUD completo
import React, { useState, useEffect } from 'react';
import {
    Typography, Button, TextField, InputAdornment,
    Pagination, CircularProgress, Box, Snackbar, Alert,
    Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle
} from '@mui/material';

import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import RouterIcon from '@mui/icons-material/Router';

import api from '../api';
import '../styles/NetworkDevices.css';
import NetworkDeviceCard from '../components/NetworkDeviceCard';
import NetworkDeviceModal from '../components/NetworkDeviceModal';

import { API_PATH_NETWORK_DEVICES } from '../constants';

const NetworkDevices = () => {
    const [networkDevices, setNetworkDevices] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const pageSize = 10;

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [deviceToDelete, setDeviceToDelete] = useState(null);

    const fetchNetworkDevices = async () => {
        setLoading(true);
        try {
            const response = await api.get(API_PATH_NETWORK_DEVICES, {
                params: { page }
            });

            const data = response.data.results ? response.data.results : response.data;
            const count = response.data.count || (Array.isArray(data) ? data.length : 0);

            setNetworkDevices(Array.isArray(data) ? data : []);
            setTotalPages(Math.ceil(count / pageSize));

        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar los dispositivos de red', severity: 'error' });
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchNetworkDevices();
    }, [page]);

    // Funciones para abrir y cerrar el modal de crear o editar
    const handleOpenModal = (device = null) => {
        setSelectedDevice(device);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setSelectedDevice(null);
        setIsModalOpen(false);
    };

    const handleSaveDevice = async (deviceData, deviceId) => {
        try {
            if (deviceId) {
                await api.patch(`${API_PATH_NETWORK_DEVICES}${deviceId}/`, deviceData);
                setNotification({ open: true, message: 'Dispositivo actualizado correctamente', severity: 'success' });
            } else {
                await api.post(API_PATH_NETWORK_DEVICES, deviceData);
                setNotification({ open: true, message: 'Dispositivo creado correctamente', severity: 'success' });
            }
            fetchNetworkDevices();
            handleCloseModal();
        } catch (err) {
            // Manejo de errores del backend
            const data = err.response?.data;
            if (data) {
                // Errores de validacion por campo
                const messages = [];
                for (const [field, fieldErrors] of Object.entries(data)) {
                    const fieldName = {
                        name: 'Nombre',
                        ip_address: 'Dirección IP',
                        username: 'Usuario',
                        password: 'Contraseña',
                        api_port: 'Puerto API'
                    }[field] || field;

                    const errorText = Array.isArray(fieldErrors) ? fieldErrors.join(', ') : fieldErrors;
                    messages.push(`${fieldName}: ${errorText}`);
                }
                const errorMessage = messages.length > 0
                    ? messages.join(' | ')
                    : 'No se ha podido guardar el dispositivo';
                setNotification({ open: true, message: errorMessage, severity: 'warning' });
            } else {
                setNotification({ open: true, message: 'Error de conexión con el servidor', severity: 'error' });
            }
        }
    };

    // Funciones para el dialogo de confirmacion de borrado
    const handleOpenDeleteDialog = (device) => {
        setDeviceToDelete(device);
        setIsDeleteDialogOpen(true);
    };

    const handleCloseDeleteDialog = () => {
        setDeviceToDelete(null);
        setIsDeleteDialogOpen(false);
    };

    const handleConfirmDelete = async () => {
        try {
            await api.delete(`${API_PATH_NETWORK_DEVICES}${deviceToDelete.id}/`);
            setNotification({ open: true, message: 'Dispositivo eliminado correctamente', severity: 'success' });
            fetchNetworkDevices();
            handleCloseDeleteDialog();
        } catch (err) {
            const detail = err.response?.data?.detail || 'No se ha podido eliminar el dispositivo';
            setNotification({ open: true, message: detail, severity: 'warning' });
        }
    };

    const handlePageChange = (event, value) => {
        setPage(value);
    };

    return (
        <div className="network-devices-container">
            <div className="network-devices-header">
                <Typography variant="h5" className="network-devices-header-title">
                    <RouterIcon sx={{ color: 'var(--accent-color)', fontSize: 28 }} />
                    Switches / Routers
                </Typography>

                <div className="network-devices-header-actions">
                    <div className="permission-search-input">
                        <TextField
                            size="small"
                            placeholder="Buscar dispositivo..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <SearchIcon />
                                    </InputAdornment>
                                ),
                            }}
                        />
                    </div>
                    <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => handleOpenModal()}
                        className="new-network-device-button"
                    >
                        Nuevo Dispositivo
                    </Button>
                </div>
            </div>

            <div className="network-devices-list">
                {loading ? (
                    <Box className="loading-spinner-container">
                        <CircularProgress className="loading-spinner" />
                    </Box>
                ) : (
                    networkDevices
                        .filter(d => d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                     d.ip_address.toLowerCase().includes(searchTerm.toLowerCase()))
                        .map((device) => (
                            <NetworkDeviceCard
                                key={device.id}
                                networkDevice={device}
                                onEdit={handleOpenModal}
                                onDelete={handleOpenDeleteDialog}
                            />
                        ))
                )}

                {!loading && networkDevices.length === 0 && (
                    <Typography className="no-network-devices-message">
                        No se encontraron dispositivos de red
                    </Typography>
                )}
            </div>

            <div className="network-devices-pagination">
                <Pagination
                    count={totalPages}
                    page={page}
                    onChange={handlePageChange}
                    variant="outlined"
                    shape="rounded"
                    showFirstButton
                    showLastButton
                />
            </div>

            <NetworkDeviceModal
                open={isModalOpen}
                networkDevice={selectedDevice}
                onClose={handleCloseModal}
                onSave={handleSaveDevice}
            />

            <Dialog open={isDeleteDialogOpen} onClose={handleCloseDeleteDialog} PaperProps={{ className: "modal-paper" }}>
                <DialogTitle sx={{ color: 'var(--text-primary)' }}>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{ color: 'var(--text-light)' }}>
                        ¿Estás seguro de que quieres eliminar el dispositivo "{deviceToDelete?.name}"? Esta acción no se puede deshacer.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDeleteDialog} sx={{ color: 'var(--text-secondary)' }}>Cancelar</Button>
                    <Button onClick={handleConfirmDelete} sx={{ color: 'var(--danger-color)' }} autoFocus>
                        Eliminar
                    </Button>
                </DialogActions>
            </Dialog>

            <Snackbar
                open={notification.open}
                autoHideDuration={4000}
                onClose={() => setNotification({ ...notification, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert severity={notification.severity} variant="filled" sx={{ width: '100%' }}>
                    {notification.message}
                </Alert>
            </Snackbar>
        </div>
    );
};

export default NetworkDevices;
