// new_component.v  // avalon_MM_slave that also uses "address" 
// -- Sachin B. Patkar 
`timescale 1 ps / 1 ps
module new_component (
        input  wire        clock_sink_clk,         //   clock_sink.clk
        input  wire [7:0]  avalon_slave_address,   // avalon_slave.address
        input  wire        avalon_slave_read,      //             .read
        output reg [31:0] avalon_slave_readdata,  //             .readdata
        input  wire        avalon_slave_write,     //             .write
        input  wire [31:0] avalon_slave_writedata, //             .writedata
        input  wire        reset_sink_resetn       //   reset_sink.reset_n
    );
  reg [31:0] command_word, status_word, sig_inp, sig_outp ;
  localparam [7:0] ADDR_COMMAND_WORD = 1, ADDR_STATUS_WORD=2, 
             ADDR_INP_WORD=3 , ADDR_OUTP_WORD=4 ;
  localparam FLIP_BITS_CMD = 32'd1 ;
  always @(*) begin
    if ( avalon_slave_read ) begin 
      case ( avalon_slave_address )
        ADDR_STATUS_WORD : avalon_slave_readdata = status_word ;
        ADDR_OUTP_WORD : avalon_slave_readdata = sig_outp ;
        default : avalon_slave_readdata = 0 ;
      endcase
    end
  end

  reg command_start ;
  // synchronous updates on command_word and  
  always  @( posedge clock_sink_clk ) begin
    if ( reset_sink_resetn==0 ) begin 
      command_word <= 0 ; command_start <= 0 ;
    end else begin
      if ( avalon_slave_write && (avalon_slave_address==ADDR_COMMAND_WORD) ) begin 
        command_word <= avalon_slave_writedata ;
        command_start <= 1 ;
      end  else begin command_start <= 0 ; end
    end
  end
  // synchronous updates on sig_inp
  always  @( posedge clock_sink_clk ) begin
    if ( reset_sink_resetn==0 ) begin sig_inp <= 0 ;
    end else begin
      if ( avalon_slave_write && (avalon_slave_address==ADDR_INP_WORD) ) begin 
        sig_inp <= avalon_slave_writedata ;
      end 
    end
  end
  reg [1:0] state_flip_bits_cmd ;
  // synchronous updates on status_word
  always  @( posedge clock_sink_clk ) begin
    if ( reset_sink_resetn==0 ) begin status_word <= 0 ;
    end else begin
      if ( avalon_slave_write && (avalon_slave_address==ADDR_STATUS_WORD) ) begin
        status_word <= 0 ;
      end else if ( command_word==FLIP_BITS_CMD && (state_flip_bits_cmd==3) ) begin 
        status_word <= 1 ;
      end
    end
  end
  // synchronous updates on sig_outp and state_flip_bits_cmd
  always  @( posedge clock_sink_clk ) begin
    if ( reset_sink_resetn==0 ) begin sig_outp <= 32'h0 ; 
      state_flip_bits_cmd <= 0 ;
    end else begin
      if ( command_start==1 && (command_word==FLIP_BITS_CMD)) begin 
//        $display("flip_bits_cmd starting") ;
        state_flip_bits_cmd <= 1 ; 
      end else if ( state_flip_bits_cmd == 1 ) begin
//        $display("flip_bits_cmd is in state 1") ;
        sig_outp[15:0] <= ~sig_inp[15:0] ;
        state_flip_bits_cmd <= 2 ; 
      end else if ( state_flip_bits_cmd == 2 ) begin
//        $display("flip_bits_cmd is in state 2") ;
        sig_outp[31:16] <= ~sig_inp[31:16] ;
        state_flip_bits_cmd <= 3 ; 
      end 
    end
  end
endmodule