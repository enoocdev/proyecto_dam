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
                    bgcolor: '#1e1e1e',
                    color: '#fff',
                    border: '1px solid #333',
                    minWidth: 200,
                    maxHeight: 300,
                    mt: 1
                }
            }}
        >

            <Box 
                className="permission-search-box" 
                sx={{ p: 1, position: 'sticky', top: 0, bgcolor: '#1e1e1e', zIndex: 2, borderBottom: '1px solid #333' }}
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
                                    <SearchIcon fontSize="small" sx={{ color: '#666' }} />
                                </InputAdornment>
                            ),
                            style: { color: 'white', fontSize: '0.9rem' } 
                        },
                    }}
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            backgroundColor: '#121212',
                            '& fieldset': { borderColor: '#333' },
                            '&:hover fieldset': { borderColor: '#555' },
                            '&.Mui-focused fieldset': { borderColor: '#8b5cf6' },
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
                            '&:hover': { bgcolor: '#333' }, 
                            gap: 1, 
                            fontSize: '0.9rem',
                            display: 'flex',
                            alignItems: 'center'
                        }}
                    >
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#8b5cf6' }} />
                        {perm.name}
                    </MenuItem>
                ))
            ) : (
                <Typography variant="caption" sx={{ p: 2, display: 'block', textAlign: 'center', color: '#666' }}>
                    {searchTerm ? "No hay coincidencias" : "No hay permisos disponibles"}
                </Typography>
            )}
        </Menu>
    );
};

export default PermissionsMenu;