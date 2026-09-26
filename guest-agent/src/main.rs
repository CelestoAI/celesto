use clap::Parser;
use celesto_guest_agent::{docker, handler, server, terminal};
use tokio::sync::watch;

#[derive(Parser)]
#[command(name = "celesto-guest-agent", about = "Celesto guest control agent")]
struct Args {
    /// Listen address. Public builds default to vsock://1024.
    #[arg(long, default_value = server::DEFAULT_LISTEN)]
    listen: String,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()),
        )
        .compact()
        .init();

    let args = Args::parse();

    // Optional: apt DPkg hooks can SIGUSR1 this PID to wake Docker discovery
    // early. Discovery also polls every 2s, so the pid file is not required.
    if let Err(error) = std::fs::write(
        "/run/celesto-guest-agent.pid",
        std::process::id().to_string(),
    ) {
        tracing::warn!(%error, "failed to write guest-agent pid file");
    }

    let (docker_rescan_tx, docker_rescan_rx) = watch::channel(0u64);
    tokio::spawn(docker::run(docker_rescan_rx));
    tokio::spawn(async move {
        #[cfg(unix)]
        {
            use tokio::signal::unix::{SignalKind, signal};
            let Ok(mut signal) = signal(SignalKind::user_defined1()) else {
                tracing::warn!("failed to install Docker rescan signal handler");
                return;
            };
            let mut generation = 0u64;
            while signal.recv().await.is_some() {
                generation = generation.wrapping_add(1);
                let _ = docker_rescan_tx.send(generation);
            }
        }
    });

    let app = handler::router();
    if args.listen.starts_with("vsock://") {
        tokio::select! {
            _ = server::serve_listen_addr(app, &args.listen) => {},
            _ = terminal::serve_vsock_terminal(terminal::DEFAULT_TERMINAL_PORT) => {},
        }
    } else {
        server::serve_listen_addr(app, &args.listen).await;
    }
}
