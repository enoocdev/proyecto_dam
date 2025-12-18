import React, { use, useEffect, useState } from 'react';
import {
    Box, Typography, CircularProgress, Snackbar, Alert, Button, Dialog, DialogTitle, IconButton, DialogContent, DialogActions, TextField, Menu, MenuItem,Chip 
} from '@mui/material';

import GroupIcon from '@mui/icons-material/Group';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import useEndpointPermissions from "../hooks/useEndpointPermissions"
import UserGroup from "../components/UserGroup"

import RestrictedAccess from '../components/RestrictedAccess';
import { ACCESS_TOKEN, USER_PERMISSIONS } from '../constants';
import api from '../api';
import '../styles/UserGroups.css';

const API_PATH_USER_GROUPS = "/users-groups/"
const API_PATH_PERMISIONS = "/permissions/"

const UserGroups = () => {
    const user = JSON.parse(localStorage.getItem(USER_PERMISSIONS))
    const [loading, setloading] = useState(false);
    const [groups, setGroups] = useState([]);
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
    const [allPermissions, setAllPermissions] = useState([]);
    const [avaliablePermissions, setAvaliablePermissions] = useState([]);
    const [open, setOpen] = useState(false);
    const [newGroupPermisions, setNewGroupPermisions] = useState([])
    const [newName, setNewName] =   useState()

    // const idPermisisons = [...newGroup.permissions]

    //     idPermisisons.push(perm.id)

    //     setNewGroup(
    //         [
    //             newGroup.name,
    //             idPermisisons
                
    //         ]
    //     )
    const [anchorEl, setAnchorEl] = useState(null);

    const fetchUserGroups = async () => {
            setloading(true)
            try {
                const { data, status } = await api.get(API_PATH_USER_GROUPS)
                if (status === 200) {
                    setGroups(
                        [
                            ...data
                        ]
                    )

                }
            } catch (err) {
                setNotification({ open: true, message: 'Error al cargar los grupos', severity: 'error' })
            }


            setloading(false)
        }

    useEffect(() => {

        const fetchPermissions = async () => {
            try {
                const { data, status } = await api.get(API_PATH_PERMISIONS)
                if (status === 200) {
                    setAllPermissions(
                        [
                            ...data
                        ]
                    )

                    setAvaliablePermissions(
                        [
                            ...data
                        ]
                    )


                }
            } catch (err) {
                setNotification({ open: true, message: 'Error al cargar los permisos', severity: 'warning' })
            }

        }


        

        fetchUserGroups()
        fetchPermissions()

    }, [])

    

    const handleOpenMenu = (event) => setAnchorEl(event.currentTarget);
    const handleCloseMenu = () => setAnchorEl(null);

    //gestion del meno du los permisos
    // añadir un permisos al nuevo  grupo
    const handleAddPermission = (perm) => {
        setNewGroupPermisions(
            [
                ...newGroupPermisions,
                perm
            ]
        )
    }
    // eliminar un permisos al nuevo  grupo
    const handleDeletePermission   = (perm) => {
        setNewGroupPermisions(
            [
            ...newGroupPermisions.filter((permission) => permission.id !=  perm)
            ]
        )
    }

    // Ir modificando la lista de los permisos disponibles cada vez que cambia los permisos del grupo
    useEffect(() => {
        setAvaliablePermissions(
            [
                ...allPermissions.filter((p) => !newGroupPermisions.includes(p))
            ]
        )
        
    }, [newGroupPermisions])


    const handleOpenGroup = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false)
        setNewName("")
        setNewGroupPermisions([])
    }

    const handleSaveChanges = () => {
        
        const newGroup = 
            {
                name : newName,
                permissions: [...newGroupPermisions.map((p) => p.id)]
            }
        

        console.log(newGroup)
        const createGroup = async () =>{
            try{

                const {status} = await api.post(API_PATH_USER_GROUPS, newGroup)

                if(status < 300){
                    setNotification({ open: true, message: 'Grupo creado correctamente', severity: 'information' })
                    fetchUserGroups()
                }else{
                    throw new Error()
                }

            }catch(err){
                setNotification({ open: true, message: 'No se ha podido crear el grupo', severity: 'error' })
            }
        }

        createGroup()
        handleClose()
    };

    const handleChangeGroup = (event) => {
        let name  = event.target.value
        setNewName(name)
    }


    return (

        <div className="groups-container">
            {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <CircularProgress sx={{ color: '#8b5cf6' }} />
                </Box>
            )}

            {!loading && !user.is_superuser && !user.permissions.includes("auth.view_group") && (
                <RestrictedAccess />
            )}
            {
                !loading &&
                (user.is_superuser || user.permissions.includes("auth.view_group")) &&
                (
                    <>
                        <Box className="groups-header">
                            <Typography variant="h5" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                                <GroupIcon sx={{ color: '#8b5cf6' }} />
                                Grupos

                            </Typography>
                            <Button
                                variant="contained"
                                startIcon={<AddIcon />}
                                onClick={handleOpenGroup}
                                sx={{
                                    backgroundColor: '#8b5cf6',
                                    color: '#fff',
                                    fontWeight: 'bold',
                                    textTransform: 'none',
                                    borderRadius: '10px',
                                    padding: '5px 14px',

                                }}
                            >
                                Crear Grupo
                            </Button>
                        </Box>
                        <div className="groups-list">
                            {groups.map((group, idx) => (
                                <UserGroup key={idx} group={group} />
                            ))}
                        </div>
                        <Dialog open={open} onClose={handleClose} classes={{ paper: 'group-dialog-paper' }}>
                            <DialogTitle sx={{ borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                Crear Grupo
                                <IconButton onClick={handleClose} sx={{ color: '#aaa' }}><CloseIcon /></IconButton>
                            </DialogTitle>
                            <DialogContent sx={{ pt: 3 }}>
                                <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
                                    <TextField
                                        label="Nombre del Grupo"
                                        fullWidth
                                        value={newName}
                                        onChange={handleChangeGroup}
                                        sx={{
                                            '& .MuiInputBase-root': { color: '#fff' },
                                            '& .MuiInputLabel-root': { color: '#aaa' },
                                            '& .MuiOutlinedInput-notchedOutline': { borderColor: '#555' },
                                            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#8b5cf6' },
                                            '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#8b5cf6' },
                                        }}
                                    />
                                    <Box>
                                        <Typography variant="caption" sx={{ color: '#8b5cf6', mb: 1, display: 'block' }}>PERMISOS</Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                            {newGroupPermisions.map((perm) => (
                                                <Chip
                                                    key={perm.id}
                                                    label={perm.name}
                                                    onDelete={() => handleDeletePermission(perm.id)}
                                                    sx={{
                                                        backgroundColor: 'rgba(139, 92, 246, 0.15)',
                                                        color: '#a78bfa',
                                                        border: '1px solid rgba(139, 92, 246, 0.3)',
                                                        '& .MuiChip-deleteIcon': {
                                                            color: '#a78bfa',
                                                            '&:hover': { color: '#ff4d4d' }
                                                        }
                                                    }}
                                                />
                                            ))}


                                            <IconButton
                                                onClick={(handleOpenMenu)}
                                                size="small"
                                                sx={{
                                                    bgcolor: '#2b2d31',
                                                    color: '#8b5cf6',
                                                    border: '1px dashed #555',
                                                    width: 32, height: 32,
                                                    '&:hover': { bgcolor: '#8b5cf6', color: '#fff', borderColor: '#8b5cf6' }
                                                }}
                                            >
                                                <AddIcon fontSize="small" />
                                            </IconButton>
                                        </Box>
                                    </Box>
                                </Box>
                            </DialogContent>
                            <DialogActions sx={{ p: 3, borderTop: '1px solid #333' }}>
                                <Button variant="contained" onClick={handleSaveChanges} sx={{ bgcolor: '#8b5cf6', '&:hover': { bgcolor: '#7c3aed' } }}>Crear Grupo</Button>
                            </DialogActions>

                            <Menu
                                anchorEl={anchorEl}
                                open={Boolean(anchorEl)}
                                onClose={handleCloseMenu}
                                PaperProps={{
                                    sx: {
                                        bgcolor: '#1e1e1e', color: '#fff', border: '1px solid #333',
                                        minWidth: 200, maxHeight: 300, mt: 1
                                    }
                                }}
                            >
                                {avaliablePermissions.length > 0 ? (
                                    avaliablePermissions.map((perm) => (
                                        <MenuItem
                                            key={perm.id}
                                            onClick={() => handleAddPermission(perm)}
                                            sx={{ '&:hover': { bgcolor: '#333' }, gap: 1, fontSize: '0.9rem' }}
                                        >
                                            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#8b5cf6' }} />
                                            {perm.name}
                                        </MenuItem>
                                    ))
                                ) : (
                                    <Typography variant="caption" sx={{ p: 2, display: 'block', textAlign: 'center', color: '#666' }}>
                                        No hay permisos disponibles
                                    </Typography>
                                )}
                            </Menu>
                        </Dialog>
                    </>
                )
            }



            {/* Notificaciones */}
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

export default UserGroups;