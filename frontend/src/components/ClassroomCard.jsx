import React from 'react';
import { IconButton, Tooltip, Chip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom';
import DevicesIcon from '@mui/icons-material/Devices';

const ClassroomCard = ({ classroom, allDevices = [], onEdit, onDelete }) => {
    // Resolver IDs de devices a objetos completos
    const devicesMap = Object.fromEntries(allDevices.map(d => [d.id, d]));
    const resolvedDevices = (classroom.devices || []).map(dev =>
        typeof dev === 'object' ? dev : devicesMap[dev]
    ).filter(Boolean);

    return (
        <div className="classroom-card">
            <div className="classroom-info">
                <div className="classroom-icon">
                    <MeetingRoomIcon sx={{ fontSize: 28, color: '#8b5cf6' }} />
                </div>
                <div className="classroom-names">
                    <h4>{classroom.name}</h4>
                    <span>
                        <DevicesIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                        {resolvedDevices.length} dispositivo{resolvedDevices.length !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            <div className="classroom-devices-chips">
                {resolvedDevices.length > 0 ? (
                    <>
                        {resolvedDevices.slice(0, 4).map((device) => (
                            <Chip
                                key={device.id}
                                label={device.hostname || device.name || `#${device.id}`}
                                size="small"
                                className="device-chip"
                            />
                        ))}
                        {resolvedDevices.length > 4 && (
                            <Chip
                                label={`+${resolvedDevices.length - 4}`}
                                size="small"
                                className="device-chip device-chip--extra"
                            />
                        )}
                    </>
                ) : (
                    <span className="no-devices-text">Sin dispositivos</span>
                )}
            </div>

            <div className="classroom-actions">
                <Tooltip title="Editar Aula">
                    <IconButton
                        onClick={() => onEdit(classroom)}
                        className="action-button-edit"
                    >
                        <EditIcon />
                    </IconButton>
                </Tooltip>
                <Tooltip title="Eliminar Aula">
                    <IconButton
                        onClick={() => onDelete(classroom)}
                        className="action-button-delete"
                    >
                        <DeleteIcon />
                    </IconButton>
                </Tooltip>
            </div>
        </div>
    );
};

export default ClassroomCard;
