// Modal para crear o editar un dispositivo de red (switch/router)
// Incluye validacion de campos antes de guardar
import React, { useState, useEffect } from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions,
    TextField, Button, IconButton, Box, Typography
} from '@mui/material';
import { Close } from '@mui/icons-material';
import '../styles/UserModal.css';

const NetworkDeviceModal = ({ open, onClose, onSave, networkDevice }) => {

    const initialFormState = {
        name: '',
        ip_address: '',
        username: '',
        password: '',
        password_confirm: '',
        api_port: 8728
    };

    const [formData, setFormData] = useState(initialFormState);
    const [errors, setErrors] = useState({});

    const isEditMode = Boolean(networkDevice);

    useEffect(() => {
        if (open) {
            if (isEditMode && networkDevice) {
                setFormData({
                    name: networkDevice.name || '',
                    ip_address: networkDevice.ip_address || '',
                    username: networkDevice.username || '',
                    password: '',
                    password_confirm: '',
                    api_port: networkDevice.api_port ?? 8728
                });
            } else {
                setFormData(initialFormState);
            }
            setErrors({});
        }
    }, [networkDevice, open, isEditMode]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        // Limpia el error del campo al escribir
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
        // Limpiar error de confirmacion si se modifica cualquier campo de contraseña
        if ((name === 'password' || name === 'password_confirm') && errors.password_confirm) {
            setErrors(prev => ({ ...prev, password_confirm: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.name.trim()) {
            newErrors.name = 'El nombre es obligatorio';
        } else if (formData.name.length > 50) {
            newErrors.name = 'El nombre no puede superar los 50 caracteres';
        }

        if (!formData.ip_address.trim()) {
            newErrors.ip_address = 'La dirección IP es obligatoria';
        } else {
            // Validacion basica de formato IPv4
            const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
            if (!ipRegex.test(formData.ip_address)) {
                newErrors.ip_address = 'Formato de IP no válido (ej: 192.168.1.1)';
            } else {
                const parts = formData.ip_address.split('.');
                const valid = parts.every(p => parseInt(p) >= 0 && parseInt(p) <= 255);
                if (!valid) {
                    newErrors.ip_address = 'Cada octeto debe estar entre 0 y 255';
                }
            }
        }

        if (!formData.username.trim()) {
            newErrors.username = 'El usuario es obligatorio';
        } else if (formData.username.length > 50) {
            newErrors.username = 'El usuario no puede superar los 50 caracteres';
        }

        const isChangingPassword = formData.password || formData.password_confirm;

        if (!isEditMode && !formData.password.trim()) {
            newErrors.password = 'La contraseña es obligatoria';
        }

        if (isChangingPassword && formData.password !== formData.password_confirm) {
            newErrors.password_confirm = 'Las contraseñas no coinciden';
        }

        const port = parseInt(formData.api_port);
        if (formData.api_port === '' || formData.api_port === null || formData.api_port === undefined) {
            newErrors.api_port = 'El puerto es obligatorio';
        } else if (isNaN(port) || port < 1 || port > 65535) {
            newErrors.api_port = 'El puerto debe estar entre 1 y 65535';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSave = () => {
        if (!validateForm()) return;

        const dataToSave = {
            name: formData.name.trim(),
            ip_address: formData.ip_address.trim(),
            username: formData.username.trim(),
            api_port: parseInt(formData.api_port)
        };

        // Solo enviar password si se ha rellenado
        if (formData.password.trim()) {
            dataToSave.password = formData.password;
        }

        const deviceId = networkDevice ? networkDevice.id : null;
        onSave(dataToSave, deviceId);
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
                {isEditMode ? 'Editar Dispositivo de Red' : 'Nuevo Dispositivo de Red'}
                <IconButton onClick={onClose} className="close-button">
                    <Close />
                </IconButton>
            </DialogTitle>

            <DialogContent className="modal-content">
                <Box component="form" className="form-container">
                    <TextField
                        name="name"
                        placeholder="Nombre del dispositivo"
                        label="Nombre"
                        value={formData.name}
                        onChange={handleChange}
                        fullWidth
                        className="dark-input"
                        variant="outlined"
                        error={Boolean(errors.name)}
                        helperText={errors.name}
                        inputProps={{ maxLength: 50 }}
                    />

                    <TextField
                        name="ip_address"
                        placeholder="192.168.1.1"
                        label="Dirección IP"
                        value={formData.ip_address}
                        onChange={handleChange}
                        fullWidth
                        className="dark-input"
                        variant="outlined"
                        error={Boolean(errors.ip_address)}
                        helperText={errors.ip_address}
                    />

                    <TextField
                        name="username"
                        placeholder="Usuario de acceso"
                        label="Usuario"
                        value={formData.username}
                        onChange={handleChange}
                        fullWidth
                        className="dark-input"
                        variant="outlined"
                        error={Boolean(errors.username)}
                        helperText={errors.username}
                        inputProps={{ maxLength: 50 }}
                    />

                    <TextField
                        name="password"
                        placeholder={isEditMode ? "Dejar vacío para mantener" : "Contraseña"}
                        label="Contraseña"
                        type="password"
                        value={formData.password}
                        onChange={handleChange}
                        fullWidth
                        className="dark-input"
                        variant="outlined"
                        error={Boolean(errors.password)}
                        helperText={errors.password || (isEditMode ? 'Dejar vacío para no cambiar' : '')}
                    />

                    <TextField
                        name="password_confirm"
                        placeholder={isEditMode ? "Repetir nueva contraseña" : "Repetir contraseña"}
                        label="Confirmar Contraseña"
                        type="password"
                        value={formData.password_confirm}
                        onChange={handleChange}
                        fullWidth
                        className="dark-input"
                        variant="outlined"
                        error={Boolean(errors.password_confirm)}
                        helperText={errors.password_confirm}
                    />

                    <TextField
                        name="api_port"
                        placeholder="8728"
                        label="Puerto API"
                        type="number"
                        value={formData.api_port}
                        onChange={handleChange}
                        fullWidth
                        className="dark-input"
                        variant="outlined"
                        error={Boolean(errors.api_port)}
                        helperText={errors.api_port}
                        inputProps={{ min: 1, max: 65535 }}
                    />
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

export default NetworkDeviceModal;
