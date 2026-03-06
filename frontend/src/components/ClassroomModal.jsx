import React, { useState, useEffect } from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions,
    TextField, Button, IconButton, Typography, Box,
    Chip, Menu, MenuItem
} from '@mui/material';
import { Close, Search, AddCircleOutline } from '@mui/icons-material';
import '../styles/UserModal.css';

const ClassroomModal = ({ open, onClose, onSave, classroom, availableDevices = [] }) => {

    const initialFormState = {
        name: '',
        devices: []
    };

    const [formData, setFormData] = useState(initialFormState);
    const [deviceMenuAnchor, setDeviceMenuAnchor] = useState(null);
    const [deviceSearch, setDeviceSearch] = useState('');

    const isEditMode = Boolean(classroom);

    useEffect(() => {
        if (open) {
            if (isEditMode && classroom) {
                // Resolver IDs de devices a objetos completos
                const devicesMap = Object.fromEntries(availableDevices.map(d => [d.id, d]));
                const resolvedDevices = (classroom.devices || []).map(dev =>
                    typeof dev === 'object' ? dev : devicesMap[dev]
                ).filter(Boolean);

                setFormData({
                    name: classroom.name || '',
                    devices: resolvedDevices
                });
            } else {
                setFormData(initialFormState);
            }
            setDeviceSearch('');
        }
    }, [classroom, open, isEditMode, availableDevices]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleOpenDeviceMenu = (event) => {
        setDeviceMenuAnchor(event.target);
    };

    const handleCloseDeviceMenu = () => {
        setDeviceMenuAnchor(null);
        setDeviceSearch('');
    };

    const handleAddDevice = (device) => {
        if (!formData.devices.some(d => d.id === device.id)) {
            setFormData(prev => ({
                ...prev,
                devices: [...prev.devices, device]
            }));
        }
        handleCloseDeviceMenu();
    };

    const handleRemoveDevice = (deviceId) => {
        setFormData(prev => ({
            ...prev,
            devices: prev.devices.filter(d => d.id !== deviceId)
        }));
    };

    const filteredAvailableDevices = availableDevices.filter(device =>
        !formData.devices.some(selected => selected.id === device.id) &&
        (device.hostname || device.name || '').toLowerCase().includes(deviceSearch.toLowerCase())
    );

    const handleSave = () => {
        const dataToSave = {
            name: formData.name,
            devices: formData.devices.map(d => d.id)
        };
        const classroomId = classroom ? classroom.id : null;
        onSave(dataToSave, classroomId);
    };

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="sm"
            fullWidth
            className="dark-modal"
            PaperProps={{ className: "modal-paper" }}
        >
            <DialogTitle className="modal-title">
                {isEditMode ? 'Editar Aula' : 'Crear Aula'}
                <IconButton onClick={onClose} className="close-button">
                    <Close />
                </IconButton>
            </DialogTitle>

            <DialogContent className="modal-content">
                <Box component="form" className="form-container">
                    <TextField
                        name="name"
                        placeholder="Nombre del Aula"
                        value={formData.name}
                        onChange={handleChange}
                        fullWidth
                        className="dark-input"
                        variant="outlined"
                    />

                    {/* Sección Dispositivos */}
                    <Box className="groups-section">
                        <Typography variant="caption" className="section-label">
                            DISPOSITIVOS
                        </Typography>

                        <Box className="chips-container">
                            {formData.devices.map((device) => (
                                <Chip
                                    key={device.id}
                                    label={device.hostname || device.name || `#${device.id}`}
                                    onDelete={() => handleRemoveDevice(device.id)}
                                    className="permission-chip"
                                    deleteIcon={<Close style={{ color: 'var(--accent-light)', fontSize: 16 }} />}
                                />
                            ))}

                            <IconButton
                                onClick={handleOpenDeviceMenu}
                                className="add-button"
                                size="small"
                            >
                                <AddCircleOutline />
                            </IconButton>
                        </Box>

                        {/* Menú Dropdown */}
                        <Menu
                            anchorEl={deviceMenuAnchor}
                            open={Boolean(deviceMenuAnchor)}
                            onClose={handleCloseDeviceMenu}
                            classes={{ paper: 'dark-menu-paper' }}
                            anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                            transformOrigin={{ vertical: 'top', horizontal: 'left' }}
                        >
                            <Box className="menu-search-box">
                                <Search className="search-icon" />
                                <input
                                    type="text"
                                    placeholder="Buscar dispositivo..."
                                    className="menu-search-input"
                                    value={deviceSearch}
                                    onChange={(e) => setDeviceSearch(e.target.value)}
                                    autoFocus
                                />
                            </Box>

                            <Box className="menu-items-scroll">
                                {filteredAvailableDevices.length > 0 ? (
                                    filteredAvailableDevices.map((device) => (
                                        <MenuItem
                                            key={device.id}
                                            onClick={() => handleAddDevice(device)}
                                            className="dark-menu-item"
                                        >
                                            <span className="bullet-point">•</span>
                                            {device.hostname || device.name || `Dispositivo #${device.id}`}
                                        </MenuItem>
                                    ))
                                ) : (
                                    <MenuItem disabled className="dark-menu-item">
                                        No hay más dispositivos
                                    </MenuItem>
                                )}
                            </Box>
                        </Menu>
                    </Box>
                </Box>
            </DialogContent>

            <DialogActions className="modal-actions">
                <Button onClick={onClose} className="btn-cancel">
                    Cancelar
                </Button>
                <Button onClick={handleSave} className="btn-save">
                    {isEditMode ? 'Guardar' : 'Crear'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default ClassroomModal;
