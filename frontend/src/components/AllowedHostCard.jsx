// Tarjeta que muestra la informacion de un host permitido
import React from 'react';
import { IconButton, Tooltip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import DnsIcon from '@mui/icons-material/Dns';
import LanIcon from '@mui/icons-material/Lan';

const AllowedHostCard = ({ host, onEdit, onDelete }) => {
    return (
        <div className="allowed-host-card">
            <div className="allowed-host-info">
                <div className="allowed-host-icon">
                    <DnsIcon sx={{ fontSize: 28, color: 'var(--accent-color)' }} />
                </div>
                <div className="allowed-host-names">
                    <h4>{host.name}</h4>
                    <span>
                        <LanIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                        {host.ip_address}
                    </span>
                </div>
            </div>

            <div className="allowed-host-actions">
                <Tooltip title="Editar Host">
                    <IconButton
                        onClick={() => onEdit(host)}
                        className="action-button-edit"
                    >
                        <EditIcon />
                    </IconButton>
                </Tooltip>
                <Tooltip title="Eliminar Host">
                    <IconButton
                        onClick={() => onDelete(host)}
                        className="action-button-delete"
                    >
                        <DeleteIcon />
                    </IconButton>
                </Tooltip>
            </div>
        </div>
    );
};

export default AllowedHostCard;
