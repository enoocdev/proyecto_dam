import React, { useState, useEffect } from 'react';
import {
    Typography, Button, TextField, InputAdornment,
    Pagination, CircularProgress, Box, Snackbar, Alert,
    Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle
} from '@mui/material';

import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom';

import api from '../api';
import '../styles/Classrooms.css';
import ClassroomCard from '../components/ClassroomCard';
import ClassroomModal from '../components/ClassroomModal';

const API_PATH_CLASSROOMS = "/devices/classroom/";
const API_PATH_DEVICES = "/devices/devices/";

const Classroom = () => {
    const [classrooms, setClassrooms] = useState([]);
    const [allDevices, setAllDevices] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const pageSize = 10;

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedClassroom, setSelectedClassroom] = useState(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [classroomToDelete, setClassroomToDelete] = useState(null);

    const fetchClassrooms = async () => {
        setLoading(true);
        try {
            const response = await api.get(API_PATH_CLASSROOMS, {
                params: { page }
            });

            const data = response.data.results ? response.data.results : response.data;
            const count = response.data.count || (Array.isArray(data) ? data.length : 0);

            setClassrooms(Array.isArray(data) ? data : []);
            setTotalPages(Math.ceil(count / pageSize));

        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar las aulas', severity: 'error' });
        }
        setLoading(false);
    };

    const fetchDevices = async () => {
        try {
            const { data, status } = await api.get(API_PATH_DEVICES);
            if (status === 200) {
                setAllDevices(Array.isArray(data) ? data : []);
            }
        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar los dispositivos', severity: 'warning' });
        }
    };

    useEffect(() => {
        fetchDevices();
    }, []);

    useEffect(() => {
        fetchClassrooms();
    }, [page]);

    // --- Modal ---
    const handleOpenModal = (classroom = null) => {
        setSelectedClassroom(classroom);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setSelectedClassroom(null);
        setIsModalOpen(false);
    };

    const handleSaveClassroom = async (classroomData, classroomId) => {
        try {
            if (classroomId) {
                await api.patch(`${API_PATH_CLASSROOMS}${classroomId}/`, classroomData);
                setNotification({ open: true, message: 'Aula actualizada correctamente', severity: 'success' });
            } else {
                await api.post(API_PATH_CLASSROOMS, classroomData);
                setNotification({ open: true, message: 'Aula creada correctamente', severity: 'success' });
            }
            fetchClassrooms();
            fetchDevices();
            handleCloseModal();
        } catch (err) {
            setNotification({ open: true, message: 'No se ha podido guardar el aula', severity: 'warning' });
        }
    };

    // --- Delete Dialog ---
    const handleOpenDeleteDialog = (classroom) => {
        setClassroomToDelete(classroom);
        setIsDeleteDialogOpen(true);
    };

    const handleCloseDeleteDialog = () => {
        setClassroomToDelete(null);
        setIsDeleteDialogOpen(false);
    };

    const handleConfirmDelete = async () => {
        try {
            await api.delete(`${API_PATH_CLASSROOMS}${classroomToDelete.id}/`);
            setNotification({ open: true, message: 'Aula eliminada correctamente', severity: 'success' });
            fetchClassrooms();
            fetchDevices();
            handleCloseDeleteDialog();
        } catch (err) {
            setNotification({ open: true, message: 'No se ha podido eliminar el aula', severity: 'warning' });
        }
    };

    const handlePageChange = (event, value) => {
        setPage(value);
    };

    return (
        <div className="classrooms-container">
            <div className="classrooms-header">
                <Typography variant="h5" className="classrooms-header-title">
                    <MeetingRoomIcon sx={{ color: '#8b5cf6', fontSize: 28 }} />
                    Gestión de Aulas
                </Typography>

                <div className="classrooms-header-actions">
                    <div className="permission-search-input">
                        <TextField
                            size="small"
                            placeholder="Buscar aula..."
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
                        className="new-classroom-button"
                    >
                        Nueva Aula
                    </Button>
                </div>
            </div>

            <div className="classrooms-list">
                {loading ? (
                    <Box className="loading-spinner-container">
                        <CircularProgress className="loading-spinner" />
                    </Box>
                ) : (
                    classrooms
                        .filter(c => c.name.toLowerCase().includes(searchTerm.toLowerCase()))
                        .map((classroom) => (
                            <ClassroomCard
                                key={classroom.id}
                                classroom={classroom}
                                allDevices={allDevices}
                                onEdit={handleOpenModal}
                                onDelete={handleOpenDeleteDialog}
                            />
                        ))
                )}

                {!loading && classrooms.length === 0 && (
                    <Typography className="no-classrooms-message">
                        No se encontraron aulas
                    </Typography>
                )}
            </div>

            <div className="classrooms-pagination">
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

            <ClassroomModal
                open={isModalOpen}
                classroom={selectedClassroom}
                onClose={handleCloseModal}
                onSave={handleSaveClassroom}
                availableDevices={allDevices}
            />

            <Dialog open={isDeleteDialogOpen} onClose={handleCloseDeleteDialog} PaperProps={{ className: "modal-paper" }}>
                <DialogTitle sx={{ color: '#fff' }}>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{ color: '#ccc' }}>
                        ¿Estás seguro de que quieres eliminar el aula "{classroomToDelete?.name}"? Esta acción no se puede deshacer.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDeleteDialog} sx={{ color: '#aaa' }}>Cancelar</Button>
                    <Button onClick={handleConfirmDelete} sx={{ color: '#ef4444' }} autoFocus>
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

export default Classroom;