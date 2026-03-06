import React, { useState } from 'react';
import { 
    Menu, 
    Box, 
    TextField, 
    InputAdornment, 
    MenuItem, 
    Typography 
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

const PermissionsMenu = ({ anchorEl, onClose, permissions = [], onAddPermission }) => {
    const [searchTerm, setSearchTerm] = useState("");

    const filteredPermissions = permissions.filter((perm) => 
        perm.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleItemClick = (perm) => {
        onAddPermission(perm);
        setSearchTerm(""); 
        // Opcional: onClose(); // Si quieres que se cierre al seleccionar uno
    };

    return (
        <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={onClose}
            PaperProps={{
                sx: {
                    bgcolor: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                    minWidth: 200,
                    maxHeight: 300,
                    mt: 1
                }
            }}
        >

            <Box 
                className="permission-search-box" 
                sx={{ p: 1, position: 'sticky', top: 0, bgcolor: 'var(--bg-card)', zIndex: 2, borderBottom: '1px solid var(--border-color)' }}
            >
                <TextField
                    className="permission-search-input"
                    size="small"
                    fullWidth
                    placeholder="Buscar permiso..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={(e) => e.stopPropagation()}
                    autoFocus
                    slotProps={{
                        input: {
                            startAdornment: (
                                <InputAdornment position="start">
                                    <SearchIcon fontSize="small" sx={{ color: 'var(--text-dim)' }} />
                                </InputAdornment>
                            ),
                            style: { color: 'var(--text-primary)', fontSize: '0.9rem' } 
                        },
                    }}
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            backgroundColor: 'var(--bg-app)',
                            '& fieldset': { borderColor: 'var(--border-color)' },
                            '&:hover fieldset': { borderColor: 'var(--border-lighter)' },
                            '&.Mui-focused fieldset': { borderColor: 'var(--accent-color)' },
                        }
                    }}
                />
            </Box>

            {/* --- LISTA DE PERMISOS --- */}
            {filteredPermissions.length > 0 ? (
                filteredPermissions.map((perm) => (
                    <MenuItem
                        key={perm.id}
                        onClick={() => handleItemClick(perm)}
                        sx={{ 
                            '&:hover': { bgcolor: 'var(--hover-bg-strong)' }, 
                            gap: 1, 
                            fontSize: '0.9rem',
                            display: 'flex',
                            alignItems: 'center'
                        }}
                    >
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'var(--accent-color)' }} />
                        {perm.name}
                    </MenuItem>
                ))
            ) : (
                <Typography variant="caption" sx={{ p: 2, display: 'block', textAlign: 'center', color: 'var(--text-dim)' }}>
                    {searchTerm ? "No hay coincidencias" : "No hay permisos disponibles"}
                </Typography>
            )}
        </Menu>
    );
};

export default PermissionsMenu;