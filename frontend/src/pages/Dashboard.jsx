
import React, { useEffect, useState, useCallback } from 'react'; 
import {
    Box, Typography, CircularProgress,Snackbar ,Alert
} from '@mui/material';

import api from '../api';

import DeviceCard from "../components/DeviceCard";
import useDashboardSocket from "../hooks/useDashboardSocket";
import "../styles/Dashboard.css";

import {API_PATH_DEVICES, API_PATH_CLASSROOMS_WITHOUT_PAGINATION} from '../constants';



function DashboardPage() {

    const [devices, setDevices] = useState([])
    const [loading, setLoading] = useState(true)

    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1);
    const pageSize = 10;

    const [classrooms, setClassrooms] = useState([]);
    const [selectedClassroom, setSelectedClassroom] = useState(null);

    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });


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

    //WebSocket: actualizar estado de dispositivos en tiempo real
    const handleDeviceStatus = useCallback((payload) => {
        const { event, device } = payload;
        if (!device?.id) return;

        setDevices((prev) =>
            prev.map((d) =>
                d.id === device.id
                    ? { ...d, ...device, is_online: event === "online" }
                    : d
            )
        );
    }, []);

    useDashboardSocket({
        onDeviceStatus: handleDeviceStatus,
    });

    const handleClassroomChange = (classroomId) => {
        setSelectedClassroom(classroomId);
    };

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
                            onShutdown={(d) => console.log("Apagar:", d.hostname)}
                            onBlockInternet={(d) => console.log("Cortar conexión:", d.hostname)}
                        />
                    ))}
                </div>
            </div>
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