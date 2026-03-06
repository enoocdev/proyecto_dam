import { useState } from "react";
import {
    Card,
    CardActionArea,
    Box,
    Typography,
    Chip,
    Drawer,
    IconButton,
    Button,
    Divider,
} from "@mui/material";
import ComputerIcon from "@mui/icons-material/Computer";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import PublicIcon from "@mui/icons-material/Public";
import PublicOffIcon from "@mui/icons-material/PublicOff";
import PowerSettingsNewIcon from "@mui/icons-material/PowerSettingsNew";
import WifiOffIcon from "@mui/icons-material/WifiOff";
import WifiIcon from "@mui/icons-material/Wifi";
import DeleteIcon from "@mui/icons-material/Delete";
import CloseIcon from "@mui/icons-material/Close";
import "../styles/DeviceCard.css";

function DeviceCard({ device, onShutdown, onBlockInternet, onUnblockInternet, onDelete }) {
    const [sheetOpen, setSheetOpen] = useState(false);

    const handleCardClick = () => setSheetOpen(true);
    const handleClose = () => setSheetOpen(false);

    const handleShutdown = () => {
        onShutdown?.(device);
        handleClose();
    };

    const handleToggleInternet = () => {
        if (device.is_internet_blocked) {
            onUnblockInternet?.(device);
        } else {
            onBlockInternet?.(device);
        }
        handleClose();
    };

    const handleDelete = () => {
        onDelete?.(device);
        handleClose();
    };

    return (
        <>
            {/*Equipo*/}
            <Card className={`device-card ${device.is_online ? "device-card--online" : "device-card--offline"}`}>
                <CardActionArea onClick={handleCardClick} className="device-card__action-area">

                    {/* En un futura imagen de pantalla del equipo */}
                    <Box className="device-card__preview">
                        <ComputerIcon className="device-card__preview-icon" />
                    </Box>

                    <Box className="device-card__body">
                        <Typography variant="subtitle1" className="device-card__hostname">
                            {device.hostname}
                        </Typography>

                        <Typography variant="caption" className="device-card__ip">
                            {device.ip}
                        </Typography>

                        {/* chips de estado */}
                        <Box className="device-card__badges">
                            <Chip
                                icon={<FiberManualRecordIcon className="badge-dot" />}
                                label={device.is_online ? "Encendido" : "Apagado"}
                                size="small"
                                className={`device-badge ${device.is_online ? "badge--online" : "badge--offline"}`}
                            />

                            <Chip
                                icon={
                                    device.is_internet_blocked
                                        ? <PublicOffIcon className="badge-icon" />
                                        : <PublicIcon className="badge-icon" />
                                }
                                label={device.is_internet_blocked ? "Bloqueado" : "Internet"}
                                size="small"
                                className={`device-badge ${device.is_internet_blocked ? "badge--blocked" : "badge--internet"}`}
                            />
                        </Box>
                    </Box>
                </CardActionArea>
            </Card>

            {/* BOTTOM ACTION SHEET*/}
            <Drawer
                anchor="bottom"
                open={sheetOpen}
                onClose={handleClose}
                className="action-sheet"
            >
                <div className="action-sheet__handle" />

                <div className="action-sheet__header">
                    <div className="action-sheet__device-info">
                        <ComputerIcon className="action-sheet__device-icon" />
                        <div>
                            <Typography variant="subtitle1" className="action-sheet__title">
                                {device.hostname}
                            </Typography>
                            <Typography variant="caption" className="action-sheet__subtitle">
                                {device.ip} · {device.mac}
                            </Typography>
                        </div>
                    </div>

                    <IconButton onClick={handleClose} size="small" className="action-sheet__close">
                        <CloseIcon sx={{ fontSize: 20 }} />
                    </IconButton>
                </div>

                <Divider className="action-sheet__divider" />

                {/* Botones de acción */}
                <div className="action-sheet__actions">
                    <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<PowerSettingsNewIcon />}
                        onClick={handleShutdown}
                        className="action-btn action-btn--shutdown"
                    >
                        Apagar equipo
                    </Button>

                    <Button
                        fullWidth
                        variant="outlined"
                        startIcon={device.is_internet_blocked ? <WifiIcon /> : <WifiOffIcon />}
                        onClick={handleToggleInternet}
                        className={`action-btn ${device.is_internet_blocked ? "action-btn--unblock" : "action-btn--block"}`}
                    >
                        {device.is_internet_blocked ? "Activar conexión" : "Cortar conexión"}
                    </Button>

                    <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<DeleteIcon />}
                        onClick={handleDelete}
                        className="action-btn action-btn--delete"
                    >
                        Eliminar equipo
                    </Button>
                </div>
            </Drawer>
        </>
    );
}

export default DeviceCard;