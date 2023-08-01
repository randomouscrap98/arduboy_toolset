use log::debug;
use simple_logger::SimpleLogger;

use crate::config::Config;

mod config;
mod scan;

const CONFIGNAME: &str = "config";

fn main() {
    SimpleLogger::new().init().unwrap();

    let config = Config::read_with_environment_toml(CONFIGNAME, None);
    debug!("Config: {:#?}", config);

    let devices = config.get_connected_devices().expect("No ports found!");

    if devices.len() > 0
    {
        println!("Found devices: {devices:#?}");
    }
    else
    {
        println!("No devices connected!");
    }
}

