use clap::Parser;
use log::{trace, info};
use simple_logger::SimpleLogger;

use crate::config::Config;

mod config;
mod scan;
mod ui;

const CONFIGNAME: &str = "config";

#[derive(Parser,Default,Debug)]
#[clap(author="haloopdy", version)]
/// A basic toolset for Arduboy
struct RunArguments
{
    /// Which action to perform
    command: Option<String>,

    #[clap(short, long)]
    /// File to perform action on or into
    file: Option<String>
}

fn main() {
    SimpleLogger::new().with_level(log::LevelFilter::Info).env().init().unwrap();

    let args = RunArguments::parse();
    let config = Config::read_with_environment_toml(CONFIGNAME, None);
    trace!("Config: {:#?}", config);

    //Perform some CLI operation
    if let Some(command) = args.command {
        match command.to_ascii_lowercase().as_str()
        {
            "scan" => {
                let devices = config.get_connected_devices().expect("No ports found!");
                if devices.len() > 0 {
                    println!("Found {} device(s): ", devices.len());
                    for d in devices {
                        println!(" {}", d);
                    }
                }
                else {
                    println!("No devices connected!");
                }
            },
            _ => {
                println!("Unknown command {}", command);
            }
        }
    }
    //Spawn the UI
    else {
        info!("Spawning the UI");
    }


}

