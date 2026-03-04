
import React, { useEffect, useState, useCallback } from 'react'; 
import {
    Box, Typography, CircularProgress,
} from '@mui/material';

import api from '../api';

import DeviceCard from "../components/DeviceCard";
import useDashboardSocket from "../hooks/useDashboardSocket";
import "../styles/Dashboard.css";

const API_PATH_DEVICES = "/devices/devices/";

function DashboardPage() {

    const [devices, setDevices] = useState([])
    const [loading, setLoading] = useState(true)

    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1);
    const pageSize = 10;


    useEffect(() => {
        fetchDevices()

    },[])

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

    const fetchDevices = async () => {

        setLoading(true);
        try {
            const response = await api.get(API_PATH_DEVICES, {
                params: {
                    page: page,
                },
            });
            
            const data = response.data.results ? response.data.results : response.data;
            const count = response.data.count || (Array.isArray(data) ? data.length : 0);

            setDevices(Array.isArray(data) ? data : []);
            setTotalPages(Math.ceil(count / pageSize));

        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar los usuarios', severity: 'error' });
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
        </div>
    )


}


export default DashboardPage