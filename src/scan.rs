use crate::config::{Config, DeviceConfig};


impl Config {
    pub fn get_connected_devices(&self) -> anyhow::Result<Vec<DeviceConfig>> {
        let ports = serialport::available_ports()?;
        let mut result : Vec<DeviceConfig> = Vec::new();
        for p in ports {
            for d in &self.devices {
                if p.port_name.contains(&d.id) {
                    result.push(d.clone())
                }
            }
        }
        Ok(result)
    }
}