use std::fmt;

use serde::Deserialize;


// Overall system configuration pulled from a config file. Runtime configuration is separate.
onestop::create_config! {
    Config, OptConfig => {
        devices: Vec<DeviceConfig>,
    }
}

/// Information about each device listed in `Config`
#[derive(Deserialize, Debug, Default, Clone)]
pub struct DeviceConfig
{
    pub vid: u16,
    pub pid: u16,
    pub has_bootloader: bool,
    pub display_name: Option<String>
}

impl fmt::Display for DeviceConfig {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "VID:{:04x}|PID:{:04x}", self.vid, self.pid)?;
        if let Some(name) = &self.display_name {
            write!(f, " ({})", name)?;
        }
        if self.has_bootloader {
            write!(f, "[bootloader]")?;
        }
        Ok(())
    }
}