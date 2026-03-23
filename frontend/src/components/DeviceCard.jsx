// Tarjeta de dispositivo que muestra su estado y permite acciones
// Al pulsar se abre un panel inferior con botones de apagar bloquear y eliminar
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
import RouterIcon from "@mui/icons-material/Router";
import SettingsEthernetIcon from "@mui/icons-material/SettingsEthernet";
import "../styles/DeviceCard.css";

function DeviceCard({ device, screenshot, networkDeviceNames = {}, onShutdown, onToggleInternet, onDelete }) {
    const [sheetOpen, setSheetOpen] = useState(false);

    // Nombre del switch resuelto desde la URL del dispositivo
    const switchName = device.network_device_url
        ? networkDeviceNames[device.network_device_url] || null
        : null;
    const switchPort = device.switch_port?.trim() || null;

    const handleCardClick = () => setSheetOpen(true);
    const handleClose = () => setSheetOpen(false);

    const handleShutdown = () => {
        onShutdown?.(device);
        handleClose();
    };

    const handleToggleInternet = () => {
        onToggleInternet?.(device);
        handleClose();
    };

    const handleDelete = () => {
        onDelete?.(device);
        handleClose();
    };

    return (
        <>
            {/* Tarjeta del equipo */}
            <Card className={`device-card ${device.is_online ? "device-card--online" : "device-card--offline"}`}>
                <CardActionArea onClick={handleCardClick} className="device-card__action-area">

                    {/* Previsualizacion del equipo o captura de pantalla */}
                    <Box className="device-card__preview">
                        {screenshot ? (
                            <img
                                src={screenshot}
                                alt={`Captura de ${device.hostname}`}
                                className="device-card__screenshot"
                            />
                        ) : (
                            <ComputerIcon className="device-card__preview-icon" />
                        )}
                    </Box>

                    <Box className="device-card__body">
                        <Typography variant="subtitle1" className="device-card__hostname">
                            {device.hostname}
                        </Typography>

                        <Typography variant="caption" className="device-card__ip">
                            {device.ip}
                        </Typography>

                        {/* Chips indicadores de estado */}
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

                            {switchName && (
                                <Chip
                                    icon={<RouterIcon className="badge-icon" />}
                                    label={switchName}
                                    size="small"
                                    className="device-badge badge--switch"
                                />
                            )}

                            {switchPort && (
                                <Chip
                                    icon={<SettingsEthernetIcon className="badge-icon" />}
                                    label={`Port: ${switchPort}`}
                                    size="small"
                                    className="device-badge badge--switch"
                                />
                            )}
                        </Box>
                    </Box>
                </CardActionArea>
            </Card>

            {/* Panel de acciones del equipo */}
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
                                {switchName && ` · Switch: ${switchName}`}
                                {switchPort && ` · Puerto: ${switchPort}`}
                            </Typography>
                        </div>
                    </div>

                    <IconButton onClick={handleClose} size="small" className="action-sheet__close">
                        <CloseIcon sx={{ fontSize: 20 }} />
                    </IconButton>
                </div>

                <Divider className="action-sheet__divider" />

                {/* Botones para controlar el equipo */}
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