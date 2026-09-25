use celesto_guest_agent::{handler, port_proxy, server, terminal};
use clap::Parser;

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
    let app = handler::router();
    if args.listen.starts_with("vsock://") {
        tokio::select! {
            _ = server::serve_listen_addr(app, &args.listen) => {},
            _ = terminal::serve_vsock_terminal(terminal::DEFAULT_TERMINAL_PORT) => {},
            _ = port_proxy::serve_vsock_port_proxy(port_proxy::DEFAULT_PORT) => {},
        }
    } else {
        server::serve_listen_addr(app, &args.listen).await;
    }
}
