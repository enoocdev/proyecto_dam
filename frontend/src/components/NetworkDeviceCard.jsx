// Tarjeta que muestra la informacion de un dispositivo de red (switch/router)
import React from 'react';
import { IconButton, Tooltip, Chip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RouterIcon from '@mui/icons-material/Router';
import LanIcon from '@mui/icons-material/Lan';
import LockIcon from '@mui/icons-material/Lock';

const NetworkDeviceCard = ({ networkDevice, onEdit, onDelete }) => {
    return (
        <div className="network-device-card">
            <div className="network-device-info">
                <div className="network-device-icon">
                    <RouterIcon sx={{ fontSize: 28, color: 'var(--accent-color)' }} />
                </div>
                <div className="network-device-names">
                    <h4>{networkDevice.name}</h4>
                    <span>
                        <LanIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                        {networkDevice.ip_address}
                    </span>
                </div>
            </div>

            <div className="network-device-details">
                <Chip
                    label={`Puerto: ${networkDevice.api_port}`}
                    size="small"
                    className="network-device-chip"
                />
                <Chip
                    icon={<LockIcon sx={{ fontSize: 14 }} />}
                    label={networkDevice.username}
                    size="small"
                    className="network-device-chip"
                />
            </div>

            <div className="network-device-actions">
                <Tooltip title="Editar Dispositivo">
                    <IconButton
                        onClick={() => onEdit(networkDevice)}
                        className="action-button-edit"
                    >
                        <EditIcon />
                    </IconButton>
                </Tooltip>
                <Tooltip title="Eliminar Dispositivo">
                    <IconButton
                        onClick={() => onDelete(networkDevice)}
                        className="action-button-delete"
                    >
                        <DeleteIcon />
                    </IconButton>
                </Tooltip>
            </div>
        </div>
    );
};

export default NetworkDeviceCard;
