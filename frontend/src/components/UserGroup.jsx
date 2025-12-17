import React, { useState } from 'react';

import {
    Box, Typography, Paper, Chip, Dialog, DialogTitle, 
    DialogContent, DialogActions, Button, TextField, IconButton
} from '@mui/material';

import SecurityIcon from '@mui/icons-material/Security';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

import CloseIcon from '@mui/icons-material/Close';
import "../styles/UserGroup.css"


function UserGroup({group}){

    const [open, setOpen] = useState(false);
    const [localGroup, setLocalGroup] = useState(
        {
            id : group.id,
            name : group.name,
            permissions : group.permissions
        }
    )
    const[permissionsName, setPermisionsName]= useState()

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
                        {localGroup.permissions.map((perm, idx) => (
                            <Chip 
                                key={idx} 
                                label={perm} 
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
                                    {localGroup.permissions.map((perm, idx) => (
                                        <Chip key={idx} label={perm} className="permission-chip" />
                                    ))}
                                </Box>
                            </Box>
                        </Box>
                    </DialogContent>
                    <DialogActions sx={{ p: 3, borderTop: '1px solid #333', justifyContent: 'space-between' }}>
                        <Button startIcon={<DeleteIcon />} color="error" onClick={handleDeleteGroup}>Eliminar</Button>
                        <Button variant="contained" onClick={handleSaveChanges} sx={{ bgcolor: '#8b5cf6', '&:hover': { bgcolor: '#7c3aed' } }}>Guardar</Button>
                    </DialogActions>
                </Dialog>
        </div>
    )
}

export default UserGroup