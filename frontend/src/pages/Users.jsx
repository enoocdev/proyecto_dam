import React, { useState, useEffect } from 'react';
import { 
    Typography, 
    Button, 
    TextField, 
    InputAdornment, 
    Avatar, 
    IconButton, 
    Alert ,
    Pagination,
    CircularProgress,
    Box,
    Snackbar ,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle
} from '@mui/material';

// Iconos
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SecurityIcon from '@mui/icons-material/Security';

// Componentes, API y CSS
import api from "../api"; 
import '../styles/Users.css'; 
import UserCard from '../components/UserCard';
import UserModal from '../components/UserModal';

const API_PATH_USERS = "/users/";
const API_PATH_USER_GROUPS = "/users-groups-without-pagination/";


const Users = () => {
    const [users, setUsers] = useState([]);
    const [allUserGroups, setAllUserGroups] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
    
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const pageSize = 10;

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [userToDelete, setUserToDelete] = useState(null);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const response = await api.get(API_PATH_USERS, {
                params: {
                    page: page,
                },
            });
            
            const data = response.data.results ? response.data.results : response.data; // para que no reviente siquito  la paginacion
            const count = response.data.count || (Array.isArray(data) ? data.length : 0);

            setUsers(Array.isArray(data) ? data : []);
            setTotalPages(Math.ceil(count / pageSize));

        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar los usuarios', severity: 'error' });
        }
        setLoading(false);
    };

    const fetchUserGroups = async () => {
        try {
            const { data, status } = await api.get(API_PATH_USER_GROUPS);
            if (status === 200) {
                setAllUserGroups(data);
            }
        } catch (err) {
            setNotification({ open: true, message: 'Error al cargar los grupos', severity: 'warning' });
        }
    };

    useEffect(() => {
        
    }, []);


    useEffect(() => {
        fetchUserGroups();
        fetchUsers();

    }, [page]);

    const handleOpenModal = (user = null) => {
        setSelectedUser(user);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setSelectedUser(null);
        setIsModalOpen(false);
    };

    const handleSaveUser = async (userData, userId) => {
        try {
            if (userId) {
                await api.patch(`/users/${userId}/`, userData);
            } else {
                await api.post('/users/', userData);
            }
            fetchUsers(page); 
            handleCloseModal();
        } catch (err) {
            setNotification({ open: true, message: 'No se ha podido actualizar o gruadar el usuario', severity: 'warning' });

        }
    };

    const handleOpenDeleteDialog = (user) => {
        setUserToDelete(user);
        setIsDeleteDialogOpen(true);
    };

    const handleCloseDeleteDialog = () => {
        setUserToDelete(null);
        setIsDeleteDialogOpen(false);
    };

    const handleConfirmDelete = async () => {
        try {
            await api.delete(`/users/${userToDelete.id}/`);
            fetchUsers(page); 
            handleCloseDeleteDialog();
        } catch (error) {
            setNotification({ open: true, message: 'No se ha podido eliminar el usuario', severity: 'warning' });
        }
    };

    const handlePageChange = (event, value) => {
        setPage(value);
    };

    return (
        <div className="groups-container">
            
            <div className="groups-header">
                <Typography variant="h4" className="users-header-title">
                    Gestión de Usuarios
                </Typography>
                
                <div className="users-header-actions">
                    <div className="permission-search-input">
                         <TextField
                            size="small"
                            placeholder="Buscar usuario..."
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
                        className="new-user-button"
                    >
                        Nuevo Usuario
                    </Button>
                </div>
            </div>

            <div className="groups-list">
                {loading ? (
                    <Box className="loading-spinner-container">
                        <CircularProgress className="loading-spinner" />
                    </Box>
                ) : (
                    users
                    .filter(u => u.username.toLowerCase().includes(searchTerm.toLowerCase()))
                    .map((user) => (
                        <UserCard 
                            key={user.id}
                            user={user}
                            onEdit={handleOpenModal}
                            onDelete={handleOpenDeleteDialog}
                        />
                    ))
                )}
                
                {!loading && users.length === 0 && (
                    <Typography className="no-users-message">
                        No se encontraron usuarios
                    </Typography>
                )}
            </div>

            <div className="groups-pagination">
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

            <UserModal
                onSave={handleSaveUser}
                open={isModalOpen}
                user={selectedUser}
                onClose={handleCloseModal}
                availableGroups={allUserGroups}
            />
        

            <Dialog
                open={isDeleteDialogOpen}
                onClose={handleCloseDeleteDialog}
            >
                <DialogTitle>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        ¿Estás seguro de que quieres eliminar al usuario "{userToDelete?.username}"? Esta acción no se puede deshacer.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDeleteDialog}>Cancelar</Button>
                    <Button onClick={handleConfirmDelete} className="confirm-delete-button" autoFocus>
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

export default Users;