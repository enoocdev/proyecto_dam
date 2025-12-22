import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Grid,
    Switch,
    FormControlLabel,
    Chip,
    IconButton,
    Typography,
    Menu,
    MenuItem,
    InputAdornment,
    Box
} from '@mui/material';
import {
    Visibility,
    VisibilityOff,
    AddCircleOutline,
    Search,
    Close
} from '@mui/icons-material';
import '../styles/UserModal.css';

const UserModal = ({ open, onClose, onSave, user, availableGroups = [] }) => {

    const initialFormState = {
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        password: '',
        password_validator: '',
        is_active: true,
        is_staff: false,
        groups: []
    };

    const [formData, setFormData] = useState(initialFormState);
    const [showPassword, setShowPassword] = useState(false);
    const [passwordError, setPasswordError] = useState('');

    const [groupMenuAnchor, setGroupMenuAnchor] = useState(null);
    const [groupSearch, setGroupSearch] = useState('');

    const isEditMode = Boolean(user);

    useEffect(() => {
        if (open) {
            if (isEditMode && user) {
                setFormData({
                    username: user.username || '',
                    email: user.email || '',
                    first_name: user.first_name || '',
                    last_name: user.last_name || '',
                    password: '',
                    password_validator: '',
                    is_active: user.is_active ?? true,
                    is_staff: user.is_staff || false,
                    groups: user.groups || []
                });
            } else {
                setFormData(initialFormState);
            }
            setShowPassword(false);
            setPasswordError('');
            setGroupSearch('');
        }
    }, [user, open, isEditMode]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));

        if (name === 'password' || name === 'password_validator') {
            setPasswordError('');
        }
    };

    const handleOpenGroupMenu = (event) => {
        setGroupMenuAnchor(event.target);
    };

    const handleCloseGroupMenu = () => {
        setGroupMenuAnchor(null);
        setGroupSearch('');
    };

    const handleAddGroup = (groupToAdd) => {
        // Evitar duplicados
        if (!formData.groups.some(g => g.id === groupToAdd.id)) {
            setFormData(prev => ({
                ...prev,
                groups: [...prev.groups, groupToAdd]
            }));
        }
        handleCloseGroupMenu();
    };

    const handleRemoveGroup = (groupIdToDelete) => {
        setFormData(prev => ({
            ...prev,
            groups: prev.groups.filter(g => g.id !== groupIdToDelete)
        }));
    };

    const filteredAvailableGroups = availableGroups.filter(group =>
        !formData.groups.some(selected => selected.id === group.id) &&
        group.name.toLowerCase().includes(groupSearch.toLowerCase())
    );


    const handleSave = () => {
        if (!isEditMode || (formData.password || formData.password_validator)) {
            if (formData.password !== formData.password_validator) {
                setPasswordError('Las contraseñas no coinciden');
                return;
            }
        }

        const dataToSave = { ...formData };

        if (isEditMode && !dataToSave.password && !dataToSave.password_validator) {
            delete dataToSave.password;
            delete dataToSave.password_validator;
        }

        const userId = user ? user.id : null;
        onSave(dataToSave, userId);
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
                {isEditMode ? 'Editar Usuario' : 'Crear Usuario'}
                <IconButton onClick={onClose} className="close-button">
                    <Close />
                </IconButton>
            </DialogTitle>

            <DialogContent className="modal-content">
                <Box component="form" className="form-container">

                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <TextField
                                name="username"
                                placeholder="Nombre de Usuario"
                                value={formData.username}
                                onChange={handleChange}
                                fullWidth
                                className="dark-input"
                                variant="outlined"
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                name="email"
                                placeholder="Correo Electrónico"
                                value={formData.email}
                                onChange={handleChange}
                                fullWidth
                                className="dark-input"
                            />
                        </Grid>
                        <Grid item xs={6}>
                            <TextField
                                name="first_name"
                                placeholder="Nombre"
                                value={formData.first_name}
                                onChange={handleChange}
                                fullWidth
                                className="dark-input"
                            />
                        </Grid>
                        <Grid item xs={6}>
                            <TextField
                                name="last_name"
                                placeholder="Apellidos"
                                value={formData.last_name}
                                onChange={handleChange}
                                fullWidth
                                className="dark-input"
                            />
                        </Grid>
                    </Grid>

                    {/* Sección Contraseñas */}
                    <Box className="password-section">
                        <Grid container spacing={2}>
                            <Grid item xs={6}>
                                <TextField
                                    name="password"
                                    placeholder={isEditMode ? "Nueva Contraseña" : "Contraseña"}
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.password}
                                    onChange={handleChange}
                                    fullWidth
                                    className="dark-input"
                                    error={Boolean(passwordError)}
                                />
                            </Grid>
                            <Grid item xs={6}>
                                <TextField
                                    name="password_validator"
                                    placeholder="Repetir Contraseña"
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.password_validator}
                                    onChange={handleChange}
                                    fullWidth
                                    className="dark-input"
                                    error={Boolean(passwordError)}
                                    InputProps={{
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton
                                                    onClick={() => setShowPassword(!showPassword)}
                                                    edge="end"
                                                    className="visibility-icon"
                                                >
                                                    {showPassword ? <VisibilityOff /> : <Visibility />}
                                                </IconButton>
                                            </InputAdornment>
                                        ),
                                    }}
                                />
                            </Grid>
                        </Grid>
                        {passwordError && (
                            <Typography color="error" variant="caption" className="error-text">
                                {passwordError}
                            </Typography>
                        )}
                    </Box>

                    {/* Switches de Estado */}
                    <Box className="switches-container">
                        <FormControlLabel
                            control={
                                <Switch
                                    name="is_active"
                                    checked={formData.is_active}
                                    onChange={handleChange}
                                    className="custom-switch"
                                />
                            }
                            label="Activo"
                            className="switch-label"
                        />
                        <FormControlLabel
                            control={
                                <Switch
                                    name="is_staff"
                                    checked={formData.is_staff}
                                    onChange={handleChange}
                                    className="custom-switch"
                                />
                            }
                            label="Staff"
                            className="switch-label"
                        />
                    </Box>

                    {/* SECCIÓN GRUPOS (Abajo del todo, estilo imagen) */}
                    <Box className="groups-section">
                        <Typography variant="caption" className="section-label">
                            GRUPOS
                        </Typography>

                        <Box className="chips-container">
                            {formData.groups.map((group) => (
                                <Chip
                                    key={group.id}
                                    label={group.name}
                                    onDelete={() => handleRemoveGroup(group.id)}
                                    className="permission-chip" // Estilo morado
                                    deleteIcon={<Close style={{ color: '#a985ff', fontSize: 16 }} />}
                                />
                            ))}

                            {/* Botón + */}
                            <IconButton
                                onClick={handleOpenGroupMenu}
                                className="add-button"
                                size="small"
                            >
                                <AddCircleOutline />
                            </IconButton>
                        </Box>

                        {/* Menú Dropdown Estilo Custom */}
                        <Menu
                            anchorEl={groupMenuAnchor}
                            open={Boolean(groupMenuAnchor)}
                            onClose={handleCloseGroupMenu}
                            classes={{ paper: 'dark-menu-paper' }}
                            anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                            transformOrigin={{ vertical: 'top', horizontal: 'left' }}
                        >
                            <Box className="menu-search-box">
                                <Search className="search-icon" />
                                <input
                                    type="text"
                                    placeholder="Buscar grupo..."
                                    className="menu-search-input"
                                    value={groupSearch}
                                    onChange={(e) => setGroupSearch(e.target.value)}
                                    autoFocus
                                />
                            </Box>

                            <Box className="menu-items-scroll">
                                {filteredAvailableGroups.length > 0 ? (
                                    filteredAvailableGroups.map((group) => (
                                        <MenuItem
                                            key={group.id}
                                            onClick={() => handleAddGroup(group)}
                                            className="dark-menu-item"
                                        >
                                            <span className="bullet-point">•</span> {group.name}
                                        </MenuItem>
                                    ))
                                ) : (
                                    <MenuItem disabled className="dark-menu-item">
                                        No hay más grupos
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
                    Guardar
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default UserModal;