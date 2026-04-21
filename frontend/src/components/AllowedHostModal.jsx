// Modal para crear o editar un host permitido
// Incluye validacion de campos antes de guardar
import React, { useState, useEffect, useMemo } from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions,
    TextField, Button, IconButton, Box, Grid,
    Autocomplete
} from '@mui/material';
import { Close } from '@mui/icons-material';
import '../styles/UserModal.css';

const AllowedHostModal = ({ open, onClose, onSave, host, classrooms = [] }) => {

    const initialFormState = useMemo(() => ({
        name: '',
        ip_address: '',
        classroom: null
    }), []);

    const [formData, setFormData] = useState(initialFormState);
    const [errors, setErrors] = useState({});

    const isEditMode = Boolean(host);

    useEffect(() => {
        if (open) {
            if (isEditMode && host) {
                // eslint-disable-next-line react-hooks/set-state-in-effect
                setFormData({
                    name: host.name || '',
                    ip_address: host.ip_address || '',
                    classroom: host.classroom || null
                });
            } else {
                // eslint-disable-next-line react-hooks/set-state-in-effect
                setFormData(initialFormState);
            }
            setErrors({});
        }
    }, [host, open, isEditMode, initialFormState]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.name.trim()) {
            newErrors.name = 'El nombre es obligatorio';
        } else if (formData.name.length > 100) {
            newErrors.name = 'El nombre no puede superar los 100 caracteres';
        }

        if (!formData.ip_address.trim()) {
            newErrors.ip_address = 'La dirección IP es obligatoria';
        } else {
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

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSave = () => {
        if (!validateForm()) return;

        const dataToSave = {
            name: formData.name.trim(),
            ip_address: formData.ip_address.trim(),
            classroom: formData.classroom || null
        };

        const hostId = host ? host.id : null;
        onSave(dataToSave, hostId);
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
                {isEditMode ? 'Editar Host Permitido' : 'Nuevo Host Permitido'}
                <IconButton onClick={onClose} className="close-button">
                    <Close />
                </IconButton>
            </DialogTitle>

            <DialogContent className="modal-content">
                <Box component="form" className="form-container">
                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <TextField
                                name="name"
                                placeholder="Nombre del host"
                                value={formData.name}
                                onChange={handleChange}
                                fullWidth
                                className="dark-input"
                                variant="outlined"
                                error={Boolean(errors.name)}
                                helperText={errors.name}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                name="ip_address"
                                placeholder="Dirección IP (ej: 192.168.1.100)"
                                value={formData.ip_address}
                                onChange={handleChange}
                                fullWidth
                                className="dark-input"
                                variant="outlined"
                                error={Boolean(errors.ip_address)}
                                helperText={errors.ip_address}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <Autocomplete
                                options={classrooms}
                                getOptionLabel={(opt) => opt.name}
                                value={classrooms.find(c => c.id === formData.classroom) || null}
                                onChange={(_, val) => setFormData(prev => ({ ...prev, classroom: val ? val.id : null }))}
                                renderInput={(params) => (
                                    <TextField
                                        {...params}
                                        placeholder="Aula (opcional — vacío = global)"
                                        className="dark-input"
                                        variant="outlined"
                                    />
                                )}
                                isOptionEqualToValue={(opt, val) => opt.id === val.id}
                                fullWidth
                            />
                        </Grid>
                    </Grid>
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

export default AllowedHostModal;
