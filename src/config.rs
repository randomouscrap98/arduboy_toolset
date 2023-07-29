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
    pub id: String,
    pub has_bootloader: bool,
    pub display_name: Option<String>
}