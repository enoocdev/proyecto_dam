// Pagina de gestion de hosts permitidos
// Permite crear editar y eliminar hosts permitidos con CRUD completo
import React, { useState, useEffect } from 'react';
import {
    Typography, Button, TextField, InputAdornment,
    Pagination, CircularProgress, Box, Snackbar, Alert,
    Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle
} from '@mui/material';

import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import DnsIcon from '@mui/icons-material/Dns';

import api from '../api';
import '../styles/AllowedHosts.css';
import AllowedHostCard from '../components/AllowedHostCard';
import AllowedHostModal from '../components/AllowedHostModal';

import { API_PATH_ALLOWED_HOSTS, API_PATH_CLASSROOMS_WITHOUT_PAGINATION } from '../constants';

const AllowedHosts = () => {
    const [hosts, setHosts] = useState([]);
    const [classrooms, setClassrooms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const pageSize = 10;

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedHost, setSelectedHost] = useState(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [hostToDelete, setHostToDelete] = useState(null);

    const fetchHosts = async () => {
        setLoading(true);
        try {
            const response = await api.get(API_PATH_ALLOWED_HOSTS, {
                params: { page }
            });

            const data = response.data.results ? response.data.results : response.data;
            const count = response.data.count || (Array.isArray(data) ? data.length : 0);

            setHosts(Array.isArray(data) ? data : []);
            setTotalPages(Math.ceil(count / pageSize));

        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar los hosts permitidos', severity: 'error' });
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchHosts();
        fetchClassrooms();
    }, [page]);

    const fetchClassrooms = async () => {
        try {
            const response = await api.get(API_PATH_CLASSROOMS_WITHOUT_PAGINATION);
            setClassrooms(Array.isArray(response.data) ? response.data : []);
        } catch (err) {
            console.error('Error al cargar aulas', err);
        }
    };

    const handleOpenModal = (host = null) => {
        setSelectedHost(host);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setSelectedHost(null);
        setIsModalOpen(false);
    };

    const handleSaveHost = async (hostData, hostId) => {
        try {
            if (hostId) {
                await api.patch(`${API_PATH_ALLOWED_HOSTS}${hostId}/`, hostData);
                setNotification({ open: true, message: 'Host actualizado correctamente', severity: 'success' });
            } else {
                await api.post(API_PATH_ALLOWED_HOSTS, hostData);
                setNotification({ open: true, message: 'Host creado correctamente', severity: 'success' });
            }
            fetchHosts();
            handleCloseModal();
        } catch (err) {
            const data = err.response?.data;
            if (data) {
                const messages = [];
                for (const [field, fieldErrors] of Object.entries(data)) {
                    const fieldName = {
                        name: 'Nombre',
                        ip_address: 'Dirección IP',
                    }[field] || field;

                    const errorText = Array.isArray(fieldErrors) ? fieldErrors.join(', ') : fieldErrors;
                    messages.push(`${fieldName}: ${errorText}`);
                }
                const errorMessage = messages.length > 0
                    ? messages.join(' | ')
                    : 'No se ha podido guardar el host';
                setNotification({ open: true, message: errorMessage, severity: 'warning' });
            } else {
                setNotification({ open: true, message: 'Error de conexión con el servidor', severity: 'error' });
            }
        }
    };

    const handleOpenDeleteDialog = (host) => {
        setHostToDelete(host);
        setIsDeleteDialogOpen(true);
    };

    const handleCloseDeleteDialog = () => {
        setHostToDelete(null);
        setIsDeleteDialogOpen(false);
    };

    const handleConfirmDelete = async () => {
        try {
            await api.delete(`${API_PATH_ALLOWED_HOSTS}${hostToDelete.id}/`);
            setNotification({ open: true, message: 'Host eliminado correctamente', severity: 'success' });
            fetchHosts();
            handleCloseDeleteDialog();
        } catch (err) {
            const detail = err.response?.data?.detail || 'No se ha podido eliminar el host';
            setNotification({ open: true, message: detail, severity: 'warning' });
        }
    };

    const handlePageChange = (event, value) => {
        setPage(value);
    };

    return (
        <div className="allowed-hosts-container">
            <div className="allowed-hosts-header">
                <Typography variant="h5" className="allowed-hosts-header-title">
                    <DnsIcon sx={{ color: 'var(--accent-color)', fontSize: 28 }} />
                    Hosts Permitidos
                </Typography>

                <div className="allowed-hosts-header-actions">
                    <div className="permission-search-input">
                        <TextField
                            size="small"
                            placeholder="Buscar host..."
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
                        className="new-allowed-host-button"
                    >
                        Nuevo Host
                    </Button>
                </div>
            </div>

            <div className="allowed-hosts-list">
                {loading ? (
                    <Box className="loading-spinner-container">
                        <CircularProgress className="loading-spinner" />
                    </Box>
                ) : (
                    hosts
                        .filter(h => h.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                     h.ip_address.toLowerCase().includes(searchTerm.toLowerCase()))
                        .map((host) => (
                            <AllowedHostCard
                                key={host.id}
                                host={host}
                                onEdit={handleOpenModal}
                                onDelete={handleOpenDeleteDialog}
                            />
                        ))
                )}

                {!loading && hosts.length === 0 && (
                    <Typography className="no-allowed-hosts-message">
                        No se encontraron hosts permitidos
                    </Typography>
                )}
            </div>

            <div className="allowed-hosts-pagination">
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

            <AllowedHostModal
                open={isModalOpen}
                host={selectedHost}
                onClose={handleCloseModal}
                onSave={handleSaveHost}
                classrooms={classrooms}
            />

            <Dialog open={isDeleteDialogOpen} onClose={handleCloseDeleteDialog} PaperProps={{ className: "modal-paper" }}>
                <DialogTitle sx={{ color: 'var(--text-primary)' }}>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{ color: 'var(--text-light)' }}>
                        ¿Estás seguro de que quieres eliminar el host "{hostToDelete?.name}"? Esta acción no se puede deshacer.
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

export default AllowedHosts;
