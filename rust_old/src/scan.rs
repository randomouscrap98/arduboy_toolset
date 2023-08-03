use log::{info, debug};
use serialport::SerialPortType;

use crate::config::{Config, DeviceConfig};


impl Config {
    pub fn get_connected_devices(&self) -> anyhow::Result<Vec<DeviceConfig>> {
        let ports = serialport::available_ports()?;
        info!("Found {} available ports", ports.len());
        // debug!("Enumerated ports: {:?}", ports.iter().map(|x| x.port_name.as_str()).collect::<Vec<&str>>());
        let mut result : Vec<DeviceConfig> = Vec::new();
        for p in ports {
            match p.port_type {
                SerialPortType::UsbPort(info) => {
                    debug!("Checking device: {} ({}:{})", p.port_name, info.vid, info.pid);
                    for d in &self.devices {
                        if d.vid == info.vid && d.pid == info.pid {
                            result.push(d.clone())
                        }
                    }
                },
                _ => {
                    debug!("Ignoring non-usb port {} ({:?})", p.port_name, p.port_type);
                }
            }
        }
        Ok(result)
    }
}