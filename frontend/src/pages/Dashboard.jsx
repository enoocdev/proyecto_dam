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
import useAuth from '../hooks/useAuth';

import {API_PATH_DEVICES, API_PATH_CLASSROOMS, API_PATH_CLASSROOMS_WITHOUT_PAGINATION, API_PATH_NETWORK_DEVICES} from '../constants';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
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

    // Mapa de connected_device (ID) -> nombre del switch
    const [networkDeviceNames, setNetworkDeviceNames] = useState({});

    // Estado de bloqueo global de internet por aula
    const [classroomInternetBlocked, setClassroomInternetBlocked] = useState({});
    const [togglingGlobalInternet, setTogglingGlobalInternet] = useState(false);

    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

    // Capturas de pantalla persistidas en sessionStorage via nanostores
    const screenshots = useStore($screenshots);

    const { isSuperuser, isStaff } = useAuth();


    useEffect(() => {
        fetchClassrooms();
    }, []);

    useEffect(() => {
        fetchDevices();
    }, [selectedClassroom]);

    const fetchClassrooms = async () => {
        try {
            const response = await api.get(API_PATH_CLASSROOMS_WITHOUT_PAGINATION);
            const allData = Array.isArray(response.data) ? response.data : [];
            setClassrooms(allData);

            // Inicializar estado de bloqueo global desde datos del aula
            const blockedState = {};
            allData.forEach(c => {
                blockedState[c.id] = !!c.is_global_internet_blocked;
            });
            setClassroomInternetBlocked(blockedState);

            // Usuarios no admin: seleccionar la primera aula automaticamente
            if (!isSuperuser && !isStaff && allData.length > 0 && selectedClassroomRef.current === null) {
                handleClassroomChange(allData[0].id);
            }
        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar las Aulas', severity: 'error' });
        }
    };

    // Resuelve los nombres de los switches a partir del ID numerico de cada dispositivo
    const resolveNetworkDeviceNames = async (deviceList) => {
        const ids = [...new Set(
            deviceList
                .map(d => d.connected_device)
                .filter(Boolean)
        )];

        // Solo fetchear IDs que aun no estan resueltos
        const newIds = ids.filter(id => !networkDeviceNames[id]);
        if (newIds.length === 0) return;

        const resolved = { ...networkDeviceNames };
        await Promise.all(
            newIds.map(async (id) => {
                try {
                    const { data } = await api.get(`${API_PATH_NETWORK_DEVICES}${id}/`);
                    resolved[id] = data.name || 'Desconocido';
                } catch {
                    resolved[id] = 'Error';
                }
            })
        );
        setNetworkDeviceNames(resolved);
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
        // Usuarios no admin deben tener un aula seleccionada
        if (!isSuperuser && !isStaff && selectedClassroom === null) {
            setLoading(false);
            return;
        }

        setLoading(true);
        try {
            const params = { page };
            if (selectedClassroom !== null) {
                params.classroom = selectedClassroom;
            }

            const response = await api.get(API_PATH_DEVICES, { params });
            
            const data = response.data.results ? response.data.results : response.data;
            const count = response.data.count || (Array.isArray(data) ? data.length : 0);

            const deviceList = Array.isArray(data) ? data : [];
            setDevices(deviceList);
            setTotalPages(Math.ceil(count / pageSize));
            resolveNetworkDeviceNames(deviceList);

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

    const handleToggleInternet = async (device) => {
        const action = device.is_internet_blocked ? 'desbloquear' : 'bloquear';
        try {
            console.log(`[Dashboard] POST ${API_PATH_DEVICES}${device.id}/toggle-internet/ - ${action} internet a "${device.hostname}" (MAC: ${device.mac})`);
            const response = await api.post(`${API_PATH_DEVICES}${device.id}/toggle-internet/`);
            const willBlock = !device.is_internet_blocked;
            setDevices((prev) =>
                prev.map((d) => d.id === device.id ? { ...d,is_online: true ,is_internet_blocked: willBlock } : d)
            );
            setNotification({ open: true, message: response.data?.detail || `Internet ${willBlock ? 'bloqueado' : 'desbloqueado'} para ${device.hostname}`, severity: 'success' });
        } catch (err) {
            const detail = err.response?.data?.detail || `Error al ${action} internet de ${device.hostname}`;
            setNotification({ open: true, message: detail, severity: 'error' });
        }
    };

    // Bloquear/desbloquear internet global del aula seleccionada
    const handleToggleGlobalInternet = async () => {
        if (selectedClassroom === null) return;
        const classroom = classrooms.find(c => c.id === selectedClassroom);
        const isBlocked = classroomInternetBlocked[selectedClassroom];
        const action = isBlocked ? 'desbloquear' : 'bloquear';
        setTogglingGlobalInternet(true);
        try {
            const response = await api.post(`${API_PATH_CLASSROOMS}${selectedClassroom}/toggle-global-internet/`);
            // Leer el estado real del backend antes de actualizar la UI
            const newBlocked = response.data?.is_global_internet_blocked ?? !isBlocked;
            setClassroomInternetBlocked(prev => ({ ...prev, [selectedClassroom]: newBlocked }));

            // Actualizar estado de internet de los dispositivos del aula
            setDevices(prev => prev.map(d =>
                d.classroom === selectedClassroom ? { ...d, is_internet_blocked: newBlocked } : d
            ));

            setNotification({
                open: true,
                message: response.data?.detail || `Internet ${newBlocked ? 'bloqueado' : 'desbloqueado'} globalmente en ${classroom?.name || 'aula'}`,
                severity: 'success'
            });
        } catch (err) {
            const detail = err.response?.data?.detail || `Error al ${action} internet del aula`;
            setNotification({ open: true, message: detail, severity: 'error' });
        } finally {
            setTogglingGlobalInternet(false);
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
                {(isSuperuser || isStaff) && (
                    <button
                        className={`dashboard-filter__btn ${selectedClassroom === null ? 'dashboard-filter__btn--active' : ''}`}
                        onClick={() => handleClassroomChange(null)}
                    >
                        Todos
                    </button>
                )}
                {classrooms.map((classroom) => (
                    <button
                        key={classroom.id}
                        className={`dashboard-filter__btn ${selectedClassroom === classroom.id ? 'dashboard-filter__btn--active' : ''}`}
                        onClick={() => handleClassroomChange(classroom.id)}
                    >
                        {classroom.name}
                    </button>
                ))}

                <div className="dashboard-filter__spacer" />

                <button
                    className={`dashboard-filter__global-toggle ${classroomInternetBlocked[selectedClassroom] ? 'dashboard-filter__global-toggle--blocked' : ''}`}
                    onClick={handleToggleGlobalInternet}
                    disabled={togglingGlobalInternet || selectedClassroom === null}
                    title={selectedClassroom === null ? 'Selecciona un aula' : (classroomInternetBlocked[selectedClassroom] ? 'Desbloquear internet del aula' : 'Bloquear internet del aula')}
                >
                    {togglingGlobalInternet
                        ? <CircularProgress size={16} sx={{ color: 'inherit' }} />
                        : (classroomInternetBlocked[selectedClassroom]
                            ? <><WifiOffIcon fontSize="small" /> <span>Desbloq. Internet</span></>
                            : <><WifiIcon fontSize="small" /> <span>Bloq. Internet</span></>)
                    }
                </button>
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
                            networkDeviceNames={networkDeviceNames}
                            onShutdown={handleShutdown}
                            onToggleInternet={handleToggleInternet}
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