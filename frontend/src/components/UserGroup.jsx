// Componente de grupo que muestra su nombre y permisos
// Incluye modal de edicion donde se pueden modificar permisos y eliminar el grupo
import React, { useEffect, useState } from 'react';
import {
    Box, Typography, Paper, Chip, Dialog, DialogTitle,
    DialogContent, DialogActions, Button, TextField, IconButton
} from '@mui/material';

import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';

import api from '../api';
import PermissionsMenu from './PermissionsMenu'; 

import {API_PATH_USER_GROUPS} from '../constants';


function UserGroup({ group, allPermissions, onGroupUpdated, onGroupDelete, setNotification }) {

    const PERMISSIONS = allPermissions;
    const [open, setOpen] = useState(false);
    const [localGroup, setLocalGroup] = useState({
        id: group.id,
        name: group.name,
        permissions: group.permissions
    });

    const [anchorEl, setAnchorEl] = useState(null);
    const [avaliablePermissions, setAvaliablePermissions] = useState([]);
    const [newName, setNewName] = useState(group.name);
    const [permissions, setPermisions] = useState([]);

    const handleOpenMenu = (event) => setAnchorEl(event.currentTarget);
    const handleCloseMenu = () => setAnchorEl(null);

    useEffect(() => {
        setLocalGroup({
            id: group.id,
            name: group.name,
            permissions: group.permissions
        });
        setPermisions([...group.permissions]);
        setNewName(group.name); 
    }, [group]);

    const handleOpenGroup = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };

    const handleSaveChanges = () => {
        const newGroup = {
            id: group.id,
            name: newName,
            permissions: [...permissions.map((p) => p.id)]
        };

        const updateGroup = async () => {
            try {
                const { status } = await api.patch(API_PATH_USER_GROUPS + `${newGroup.id}/`, newGroup);
                
                if (status < 300) {
                    setNotification({ open: true, message: 'Grupo actualizado correctamente', severity: 'success' });
                    onGroupUpdated({
                        ...newGroup,
                        permissions: permissions 
                    });
                    setOpen(false);
                } else {
                    throw new Error();
                }
            } catch (err) {
                console.log(err);
                setNotification({ open: true, message: 'No se ha podido actualizado el grupo', severity: 'error' });
            }
        };

        updateGroup();
        handleClose();
    };

    const handleDeleteGroup = () => {
        const deleteGroup = async () => {
            try {
                const idGrupo = localGroup.id;
                const { status } = await api.delete(API_PATH_USER_GROUPS + `${localGroup.id}/`);

                if (status < 300) {
                    setNotification({ open: true, message: 'Grupo eliminado correctamente', severity: 'success' });
                    onGroupDelete(idGrupo);
                } else {
                    throw new Error();
                }
            } catch (err) {
                console.log(err);
                setNotification({ open: true, message: 'No se pudo eliminar el grupo', severity: 'error' });
            }
        };

        deleteGroup();
        handleClose();
    };


    // Gestion de permisos del grupo

    const handleAddPermission = (perm) => {
        setPermisions([
            ...permissions,
            perm
        ]);
    };

    const handleDeletePermission = (permId) => {
        setPermisions(permissions.filter((permission) => permission.id !== permId));
    };

    // Recalcula los permisos disponibles excluyendo los ya asignados
    useEffect(() => {
        const currentIds = permissions.map(p => p.id);
        setAvaliablePermissions(
            PERMISSIONS.filter((p) => !currentIds.includes(p.id))
        );
    }, [permissions, PERMISSIONS]);

    return (
        <div>
            <Paper
                key={localGroup.id}
                className="group-row"
                elevation={0}
                onClick={() => handleOpenGroup()}
            >
                {/* Nombre del grupo */}
                <Typography variant="body1" sx={{ fontWeight: 'bold', minWidth: '150px', color: 'var(--text-primary)' }}>
                    {localGroup.name}
                </Typography>

                {/* Permisos del grupo en forma de chips */}
                <div className="permissions-container">
                    {localGroup.permissions.map((perm) => (
                        <Chip
                            key={perm.id}
                            label={perm.name}
                            className="permission-chip"
                            size="small"
                        />
                    ))}
                </div>

                {/* Icono de edicion */}
                <EditIcon sx={{ color: 'var(--border-lighter)', fontSize: '1.1rem', minWidth: '24px' }} />
            </Paper>

            {/* Modal de edicion del grupo */}
            <Dialog open={open} onClose={handleClose} classes={{ paper: 'group-dialog-paper' }}>
                <DialogTitle sx={{ borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    Editar {localGroup.name}
                    <IconButton onClick={handleClose} sx={{ color: 'var(--text-secondary)' }}><CloseIcon /></IconButton>
                </DialogTitle>
                <DialogContent sx={{ pt: 3 }}>
                    <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
                        
                        {/* Campo de nombre del grupo */}
                        <TextField
                            label="Nombre" fullWidth value={newName} onChange={(e) => setNewName(e.target.value)}
                            sx={{
                                '& .MuiInputBase-root': { color: 'var(--text-primary)' },
                                '& .MuiInputLabel-root': { color: 'var(--text-secondary)' },
                                '& .MuiOutlinedInput-notchedOutline': { borderColor: 'var(--border-lighter)' },
                                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'var(--accent-color)' },
                            }}
                        />

                        {/* Lista de permisos del grupo con opcion de eliminar */}
                        <Box>
                            <Typography variant="caption" sx={{ color: 'var(--accent-color)', mb: 1, display: 'block' }}>PERMISOS</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {permissions.map((perm) => (
                                    <Chip
                                        key={perm.id}
                                        label={perm.name}
                                        className="permission-chip"
                                        size="small"
                                        onDelete={() => handleDeletePermission(perm.id)}
                                        sx={{
                                            backgroundColor: 'var(--accent-bg)',
                                            color: 'var(--accent-medium)',
                                            border: '1px solid var(--accent-border-strong)',
                                            '& .MuiChip-deleteIcon': {
                                                color: 'var(--accent-medium)',
                                                '&:hover': { color: 'var(--danger-color)' }
                                            }
                                        }}
                                    />
                                ))}
                                
                                {/* Boton para anadir permiso */}
                                <IconButton
                                    onClick={handleOpenMenu}
                                    size="small"
                                    sx={{
                                        bgcolor: 'var(--bg-input)', color: 'var(--accent-color)', border: '1px dashed var(--border-lighter)', width: 32, height: 32,
                                        '&:hover': { bgcolor: 'var(--accent-color)', color: 'var(--text-on-accent)', borderColor: 'var(--accent-color)' }
                                    }}
                                >
                                    <AddIcon fontSize="small" />
                                </IconButton>
                            </Box>
                        </Box>
                    </Box>
                </DialogContent>
                
                <DialogActions sx={{ p: 3, borderTop: '1px solid var(--border-color)', justifyContent: 'space-between' }}>
                    <Button startIcon={<DeleteIcon />} color="error" onClick={handleDeleteGroup}>Eliminar</Button>
                    <Button variant="contained" onClick={handleSaveChanges} sx={{ bgcolor: 'var(--accent-color)', '&:hover': { bgcolor: 'var(--accent-hover)' } }}>Guardar</Button>
                </DialogActions>

                <PermissionsMenu 
                    anchorEl={anchorEl}
                    onClose={handleCloseMenu}
                    permissions={avaliablePermissions} 
                    onAddPermission={handleAddPermission}
                />

            </Dialog>
        </div>
    );
}

export default UserGroup;