// Pagina del dashboard que muestra los equipos monitorizados en tiempo real
// Recibe actualizaciones por WebSocket y permite filtrar por aula

import React, { useEffect, useState, useCallback, useRef } from 'react'; 
import {
    Box, Typography, CircularProgress,Snackbar ,Alert
} from '@mui/material';

import api from '../api';

import DeviceCard from "../components/DeviceCard";
import useDashboardSocket from "../hooks/useDashboardSocket";
import { useStore } from "@nanostores/react";
import { $screenshots } from "../stores/screenshotStore";
import "../styles/Dashboard.css";

import {API_PATH_DEVICES, API_PATH_CLASSROOMS_WITHOUT_PAGINATION} from '../constants';
import {
    Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button
} from '@mui/material';



function DashboardPage() {

    const [devices, setDevices] = useState([])
    const [loading, setLoading] = useState(true)

    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1);
    const pageSize = 10;

    const [classrooms, setClassrooms] = useState([]);
    const [selectedClassroom, setSelectedClassroom] = useState(null);
    const selectedClassroomRef = useRef(selectedClassroom);

    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

    // Capturas de pantalla persistidas en sessionStorage via nanostores
    const screenshots = useStore($screenshots);


    useEffect(() => {
        fetchClassrooms();
    }, []);

    useEffect(() => {
        fetchDevices();
    }, [selectedClassroom]);

    const fetchClassrooms = async () => {
        try {
            const response = await api.get(API_PATH_CLASSROOMS_WITHOUT_PAGINATION);
            const data = Array.isArray(response.data) ? response.data : [];
            setClassrooms(data);
        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar las Aulas', severity: 'error' });
        }
    };

    // Actualiza el estado de los dispositivos en tiempo real via WebSocket
    const handleDeviceStatus = useCallback((payload) => {
        const { event, device } = payload;
        if (!device?.id) return;

        setDevices((prev) => {
            const exists = prev.some((d) => d.id === device.id);

            if (exists) {
                // Dispositivo conocido actualiza su estado
                return prev.map((d) =>
                    d.id === device.id
                        ? { ...d, ...device, is_online: event === "online" }
                        : d
                );
            }

            // Dispositivo nuevo que se conecta se anade si encaja con el filtro
            if (event === "online") {
                const filter = selectedClassroomRef.current;
                if (filter !== null && device.classroom !== filter) {
                    return prev; // No pertenece al aula filtrada
                }
                return [...prev, { ...device, is_online: true }];
            }

            // Dispositivo desconocido que se desconecta se ignora
            return prev;
        });
    }, []);

    // El hook del socket ya persiste las capturas en el nanostore
    useDashboardSocket({
        onDeviceStatus: handleDeviceStatus,
    });

    const handleClassroomChange = (classroomId) => {
        setSelectedClassroom(classroomId);
        selectedClassroomRef.current = classroomId;
    };

    // Estado del dialogo de confirmacion de eliminacion
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [deviceToDelete, setDeviceToDelete] = useState(null);

    const fetchDevices = async () => {

        setLoading(true);
        try {
            const params = { page };
            if (selectedClassroom !== null) {
                params.classroom = selectedClassroom;
            }

            const response = await api.get(API_PATH_DEVICES, { params });
            
            const data = response.data.results ? response.data.results : response.data;
            const count = response.data.count || (Array.isArray(data) ? data.length : 0);

            setDevices(Array.isArray(data) ? data : []);
            setTotalPages(Math.ceil(count / pageSize));

        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar los Equipos', severity: 'error' });
        }
        setLoading(false);
    };

    // Acciones sobre dispositivos

    const handleShutdown = async (device) => {
        try {
            await api.post(`${API_PATH_DEVICES}${device.id}/shutdown/`);
            setNotification({ open: true, message: `Orden de apagado enviada a ${device.hostname}`, severity: 'success' });
        } catch (err) {
            const detail = err.response?.data?.detail || `Error al apagar ${device.hostname}`;
            setNotification({ open: true, message: detail, severity: 'error' });
        }
    };

    const handleBlockInternet = async (device) => {
        try {
            // await api.post(`${API_PATH_DEVICES}${device.id}/block-internet/`);
            setDevices((prev) =>
                prev.map((d) => d.id === device.id ? { ...d, is_internet_blocked: true } : d)
            );
            setNotification({ open: true, message: `Conexión cortada a ${device.hostname}`, severity: 'success' });
        } catch {
            setNotification({ open: true, message: `Error al cortar conexión de ${device.hostname}`, severity: 'error' });
        }
    };

    const handleUnblockInternet = async (device) => {
        try {
            // await api.post(`${API_PATH_DEVICES}${device.id}/unblock-internet/`);
            setDevices((prev) =>
                prev.map((d) => d.id === device.id ? { ...d, is_internet_blocked: false } : d)
            );
            setNotification({ open: true, message: `Conexión restaurada a ${device.hostname}`, severity: 'success' });
        } catch {
            setNotification({ open: true, message: `Error al restaurar conexión de ${device.hostname}`, severity: 'error' });
        }
    };

    const handleOpenDeleteDialog = (device) => {
        setDeviceToDelete(device);
        setDeleteDialogOpen(true);
    };

    const handleCloseDeleteDialog = () => {
        setDeviceToDelete(null);
        setDeleteDialogOpen(false);
    };

    const handleConfirmDelete = async () => {
        try {
            await api.delete(`${API_PATH_DEVICES}${deviceToDelete.id}/`);
            setDevices((prev) => prev.filter((d) => d.id !== deviceToDelete.id));
            setNotification({ open: true, message: `${deviceToDelete.hostname} eliminado`, severity: 'success' });
        } catch {
            setNotification({ open: true, message: `Error al eliminar ${deviceToDelete.hostname}`, severity: 'error' });
        }
        handleCloseDeleteDialog();
    };



    return (
        <div className="dashboard-layout">

            <div className="dashboard-header">
                <Typography variant="h5" className="dashboard-header__title">
                    Dashboard
                </Typography>
                <Typography variant="body2" className="dashboard-header__subtitle">
                    Equipos en la red
                </Typography>
            </div>

            {/* Filtro por aula */}
            <div className="dashboard-filter">
                <button
                    className={`dashboard-filter__btn ${selectedClassroom === null ? 'dashboard-filter__btn--active' : ''}`}
                    onClick={() => handleClassroomChange(null)}
                >
                    Todos
                </button>
                {classrooms.map((classroom) => (
                    <button
                        key={classroom.id}
                        className={`dashboard-filter__btn ${selectedClassroom === classroom.id ? 'dashboard-filter__btn--active' : ''}`}
                        onClick={() => handleClassroomChange(classroom.id)}
                    >
                        {classroom.name}
                    </button>
                ))}
            </div>

            {/* Contenido scrollable */}
            <div className="dashboard-content">
                {loading && devices.length === 0 && (
                    <div className="dashboard-loader">
                        <CircularProgress />
                    </div>
                )}

                <div className="devices-grid">
                    {devices.map((device) => (
                        <DeviceCard
                            key={device.id}
                            device={device}
                            screenshot={screenshots[device.mac] || null}
                            onShutdown={handleShutdown}
                            onBlockInternet={handleBlockInternet}
                            onUnblockInternet={handleUnblockInternet}
                            onDelete={handleOpenDeleteDialog}
                        />
                    ))}
                </div>
            </div>

            {/* Dialogo para confirmar eliminacion */}
            <Dialog
                open={deleteDialogOpen}
                onClose={handleCloseDeleteDialog}
                PaperProps={{ className: "modal-paper" }}
            >
                <DialogTitle sx={{ color: 'var(--text-primary)' }}>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{ color: 'var(--text-light)' }}>
                        ¿Estás seguro de que quieres eliminar el equipo "{deviceToDelete?.hostname}"? Esta acción no se puede deshacer.
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
    )


}


export default DashboardPage