import React, { useEffect, useState } from 'react';

import {
    Box, Typography, Paper, Chip, Dialog, DialogTitle, 
    DialogContent, DialogActions, Button, TextField, IconButton,Menu 
} from '@mui/material';


import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

import CloseIcon from '@mui/icons-material/Close';


function UserGroup({group}){

    const [open, setOpen] = useState(false);
    const [localGroup, setLocalGroup] = useState(
        {
            id : group.id,
            name : group.name,
            permissions : group.permissions
        }
    )
    const [anchorEl, setAnchorEl] = useState(null);

    const handleOpenMenu = (event) => setAnchorEl(event.currentTarget);
    const handleCloseMenu = () => setAnchorEl(null);

    const handleOpenGroup = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false)

    }

    const handleSaveChanges = () => {
        handleClose()    
    };

    const handleDeleteGroup = () => {

        handleClose()

    };
    

    return(
        <div>
            <Paper 
                    key={localGroup.id}
                    className="group-row" 
                    elevation={0} 
                    onClick={() => handleOpenGroup()}
                    >
                    {/* 1. NOMBRE DEL GRUPO (Izquierda) */}
                    <Typography variant="body1" sx={{ fontWeight: 'bold', minWidth: '150px', color: '#fff' }}>
                        {localGroup.name}
                    </Typography>

                    {/* 2. PERMISOS (Centro/Derecha - Scrollable horizontalmente) */}
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

                    {/* 3. ICONO EDITAR (Extremo Derecha) */}
                    <EditIcon sx={{ color: '#555', fontSize: '1.1rem', minWidth: '24px' }} />
                </Paper>



                {/* --- MODAL --- */}
                <Dialog open={open} onClose={handleClose} classes={{ paper: 'group-dialog-paper' }}>
                    <DialogTitle sx={{ borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        Editar {localGroup.name}
                        <IconButton onClick={handleClose} sx={{ color: '#aaa' }}><CloseIcon /></IconButton>
                    </DialogTitle>
                    <DialogContent sx={{ pt: 3 }}>
                        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
                            <TextField
                                label="Nombre" fullWidth value={localGroup.name} onChange={(e) => setLocalGroup({ ...localGroup, name: e.target.value })}
                                sx={{
                                    '& .MuiInputBase-root': { color: '#fff' },
                                    '& .MuiInputLabel-root': { color: '#aaa' },
                                    '& .MuiOutlinedInput-notchedOutline': { borderColor: '#555' },
                                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#8b5cf6' },
                                }}
                            />
                            <Box>
                                <Typography variant="caption" sx={{ color: '#8b5cf6', mb: 1, display: 'block' }}>PERMISOS</Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                    {localGroup.permissions.map((perm) => (
                                        <Chip 
                                            key={perm.id} 
                                            label={perm.name} 
                                            className="permission-chip" 
                                            size="small" 
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
                    <DialogActions sx={{ p: 3, borderTop: '1px solid #333', justifyContent: 'space-between' }}>
                        <Button startIcon={<DeleteIcon />} color="error" onClick={handleDeleteGroup}>Eliminar</Button>
                        <Button variant="contained" onClick={handleSaveChanges} sx={{ bgcolor: '#8b5cf6', '&:hover': { bgcolor: '#7c3aed' } }}>Guardar</Button>
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
                        {/* {avaliablePermissions.length > 0 ? (
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
                        )} */}
                        <Typography variant="caption" sx={{ p: 2, display: 'block', textAlign: 'center', color: '#666' }}>
                                No hay permisos disponibles
                        </Typography>
                    </Menu>
                </Dialog>
        </div>
    )
}

export default UserGroup